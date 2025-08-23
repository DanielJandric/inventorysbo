import json
import sys
import types
import pytest


def _make_fake_openai_class(captured):
    """Return a Fake OpenAI class capturing responses.create kwargs and emitting deterministic ids."""
    counter = {"n": 0}

    class _FakeResponse:
        def __init__(self, rid: str):
            self.id = rid
            self.output_text = "OK – Réponse de test"
            self.output = [
                {
                    "id": f"msg_{rid}",
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": self.output_text, "annotations": []}],
                }
            ]

    class _FakeResponses:
        def create(self, **kwargs):
            captured.append(kwargs)
            counter["n"] += 1
            rid = f"resp{counter['n']}"
            return _FakeResponse(rid)

    class _FakeOpenAI:
        def __init__(self, *args, **kwargs):
            self._responses = _FakeResponses()
        def with_options(self, timeout=None):
            return self
        @property
        def responses(self):
            return self._responses

    return _FakeOpenAI


def _install_fake_openai(monkeypatch, fake_openai_class):
    fake_module = types.ModuleType("openai")
    fake_module.OpenAI = fake_openai_class
    monkeypatch.setitem(sys.modules, "openai", fake_module)


@pytest.fixture()
def client(monkeypatch):
    # Install a benign fake openai before importing app
    captured_boot = []
    _install_fake_openai(monkeypatch, _make_fake_openai_class(captured_boot))

    # Provide required env to bypass early halts
    monkeypatch.setenv("SUPABASE_URL", "http://localhost")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Stub supabase client
    supabase_stub = types.ModuleType("supabase")
    def _create_client(url, key):
        class _Table:
            def select(self, *a, **k):
                return self
            def order(self, *a, **k):
                return self
            def limit(self, *a, **k):
                return self
            def insert(self, *a, **k):
                return self
            def execute(self):
                return types.SimpleNamespace(data=[])
        return types.SimpleNamespace(table=lambda name: _Table())
    supabase_stub.create_client = _create_client
    monkeypatch.setitem(sys.modules, "supabase", supabase_stub)

    # Stub modules to avoid heavy initialization
    ws_stub = types.ModuleType("web_search_manager")
    ws_stub.OpenAIWebSearchManager = object
    ws_stub.WebSearchType = object
    ws_stub.WebSearchResult = object
    ws_stub.create_web_search_manager = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "web_search_manager", ws_stub)

    gsearch_stub = types.ModuleType("google_search_manager")
    gsearch_stub.GoogleSearchManager = object
    gsearch_stub.GoogleSearchType = object
    gsearch_stub.GoogleSearchResult = object
    gsearch_stub.MarketReport = object
    gsearch_stub.DailyNewsItem = object
    gsearch_stub.create_google_search_manager = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "google_search_manager", gsearch_stub)

    unified_stub = types.ModuleType("unified_market_manager")
    class _Dummy: pass
    unified_stub.UnifiedMarketManager = _Dummy
    unified_stub.StockPriceData = _Dummy
    unified_stub.MarketUpdateData = _Dummy
    unified_stub.MarketSource = _Dummy
    unified_stub.MarketUpdateType = _Dummy
    unified_stub.create_unified_market_manager = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "unified_market_manager", unified_stub)

    gcse_stub = types.ModuleType("google_cse_stock_data")
    class _GoogleCSEStockDataManager:
        def __init__(self):
            pass
    gcse_stub.GoogleCSEStockDataManager = _GoogleCSEStockDataManager
    monkeypatch.setitem(sys.modules, "google_cse_stock_data", gcse_stub)

    enh_stub = types.ModuleType("enhanced_google_cse_ai_report")
    class _EnhancedGoogleCSEAIReport: pass
    enh_stub.EnhancedGoogleCSEAIReport = _EnhancedGoogleCSEAIReport
    monkeypatch.setitem(sys.modules, "enhanced_google_cse_ai_report", enh_stub)

    scraper_stub = types.ModuleType("intelligent_scraper")
    class _Scraper: pass
    scraper_stub.IntelligentScraper = _Scraper
    scraper_stub.get_scraper = lambda *a, **k: _Scraper()
    monkeypatch.setitem(sys.modules, "intelligent_scraper", scraper_stub)

    sb_stub = types.ModuleType("scrapingbee_scraper")
    class _ScrapingBeeScraper: pass
    sb_stub.ScrapingBeeScraper = _ScrapingBeeScraper
    sb_stub.get_scrapingbee_scraper = lambda *a, **k: _ScrapingBeeScraper()
    monkeypatch.setitem(sys.modules, "scrapingbee_scraper", sb_stub)

    # Optional: stub sklearn if missing
    if "sklearn" not in sys.modules:
        skl = types.ModuleType("sklearn")
        skl_metrics = types.ModuleType("sklearn.metrics")
        skl_pair = types.ModuleType("sklearn.metrics.pairwise")
        def _cosine_similarity(X, Y=None):
            return []
        skl_pair.cosine_similarity = _cosine_similarity
        skl_feat = types.ModuleType("sklearn.feature_extraction")
        skl_text = types.ModuleType("sklearn.feature_extraction.text")
        class _TfidfVectorizer:
            def fit_transform(self, *a, **k):
                return []
        skl_text.TfidfVectorizer = _TfidfVectorizer
        sys.modules["sklearn"] = skl
        sys.modules["sklearn.metrics"] = skl_metrics
        sys.modules["sklearn.metrics.pairwise"] = skl_pair
        sys.modules["sklearn.feature_extraction"] = skl_feat
        sys.modules["sklearn.feature_extraction.text"] = skl_text

    import app as app_module
    app = app_module.app
    app.testing = True
    return app.test_client()


def test_markets_page_loads(client):
    resp = client.get("/markets")
    assert resp.status_code == 200


def test_markets_chat_success_basic(client, monkeypatch):
    import app as app_module
    captured = []
    _install_fake_openai(monkeypatch, _make_fake_openai_class(captured))

    payload = {"message": "Donne un bref resume."}
    resp = client.post("/api/markets/chat", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert isinstance(data.get("reply", ""), str) and len(data["reply"]) > 0
    # Ensure Responses API was called with typed inputs and store=true
    assert captured, "OpenAI.responses.create should have been called"
    last = captured[-1]
    assert last.get("model", "").startswith("gpt-5")
    assert last.get("store") is True
    assert isinstance(last.get("input"), list)


def test_markets_chat_stateful_previous_response_id(client, monkeypatch):
    import app as app_module
    captured = []
    _install_fake_openai(monkeypatch, _make_fake_openai_class(captured))

    session_id = "test-session-123"

    # First turn: no previous_response_id expected
    resp1 = client.post(
        "/api/markets/chat",
        data=json.dumps({"message": "Bonjour", "session_id": session_id}),
        content_type="application/json",
    )
    assert resp1.status_code == 200
    assert captured, "First call not captured"
    first_kwargs = captured[-1]
    assert "previous_response_id" not in first_kwargs

    # The server should persist the previous response id for this session
    assert session_id in app_module.responses_prev_ids
    prev_id = app_module.responses_prev_ids[session_id]
    assert isinstance(prev_id, str) and prev_id.startswith("resp")

    # Second turn: should include previous_response_id
    resp2 = client.post(
        "/api/markets/chat",
        data=json.dumps({"message": "Et la suite?", "session_id": session_id}),
        content_type="application/json",
    )
    assert resp2.status_code == 200
    assert len(captured) >= 2
    second_kwargs = captured[-1]
    assert second_kwargs.get("previous_response_id") == prev_id


def test_markets_chat_openai_unavailable(client, monkeypatch):
    # Install a module whose OpenAI class raises on init
    class _BrokenOpenAI:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("init failed")

    fake_mod = types.ModuleType("openai")
    fake_mod.OpenAI = _BrokenOpenAI
    monkeypatch.setitem(sys.modules, "openai", fake_mod)

    r = client.post(
        "/api/markets/chat",
        data=json.dumps({"message": "Ping"}),
        content_type="application/json",
    )
    assert r.status_code == 500
    body = r.get_json()
    assert body and body.get("success") is False
    assert "OpenAI" in (body.get("error") or "")


