import os
from flask import Flask
from .config import AppConfig


def create_app(config: AppConfig | None = None) -> Flask:
    cfg = config or AppConfig.from_env()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=cfg.SECRET_KEY,
        JSON_SORT_KEYS=False,
    )

    # Register blueprints
    from .blueprints.inventory import bp as inventory_bp
    from .blueprints.markets import bp as markets_bp
    from .blueprints.metrics import bp as metrics_bp

    app.register_blueprint(metrics_bp, url_prefix="/api")
    app.register_blueprint(inventory_bp, url_prefix="/api")
    app.register_blueprint(markets_bp, url_prefix="/api")

    @app.get("/")
    def health() -> str:
        return "refactored_app: ok"

    return app

