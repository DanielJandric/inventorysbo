# Web Search OpenAI Implementation

## Overview

This implementation integrates OpenAI's web search functionality into your financial information system, providing real-time market data, financial news, and comprehensive market briefings.

## Features

### 🔍 Web Search Capabilities
- **Real-time market data** from multiple sources
- **Financial news and analysis** with citations
- **Stock-specific information** with detailed analysis
- **Market alerts** for breaking news
- **Geographic localization** for region-specific data
- **Comprehensive market briefings** with structured narratives

### 📊 Search Types Available
1. **Market Data** - Current market indices, bonds, crypto, forex, commodities
2. **Financial News** - Macroeconomic news, central bank decisions, geopolitical events
3. **Stock Analysis** - Analyst recommendations, price targets, sector trends
4. **Economic Indicators** - GDP, inflation, unemployment, confidence indices
5. **Crypto Market** - Bitcoin, Ethereum, DeFi trends, regulatory news
6. **Forex Market** - Currency pairs, central bank interventions, carry trade
7. **Commodities** - Oil, precious metals, industrial metals, agricultural products
8. **Central Banks** - Monetary policy decisions, inflation outlook, rate changes
9. **Geopolitical** - International tensions, trade agreements, elections impact

## API Endpoints

### 1. Market Briefing Generation
```http
POST /api/web-search/market-briefing
Content-Type: application/json

{
  "user_location": {
    "country": "CH",
    "city": "Genève",
    "region": "Genève"
  },
  "search_context_size": "high"
}
```

**Response:**
```json
{
  "success": true,
  "briefing": "Comprehensive market analysis...",
  "timestamp": "2025-01-27T10:30:00",
  "source": "OpenAI Web Search"
}
```

### 2. Financial Markets Search
```http
POST /api/web-search/financial-markets
Content-Type: application/json

{
  "search_type": "market_data",
  "user_location": {
    "country": "CH",
    "city": "Genève"
  },
  "search_context_size": "medium"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "content": "Market data analysis...",
    "citations": [
      {
        "url": "https://example.com",
        "title": "Market Source",
        "start_index": 100,
        "end_index": 150
      }
    ],
    "search_call_id": "ws_123456",
    "timestamp": "2025-01-27T10:30:00",
    "search_type": "market_data",
    "domains_searched": ["finance.yahoo.com", "reuters.com"]
  }
}
```

### 3. Stock Information Search
```http
GET /api/web-search/stock/AAPL?location={"country":"US","city":"New York"}
```

**Response:**
```json
{
  "success": true,
  "symbol": "AAPL",
  "result": {
    "content": "Apple Inc. analysis...",
    "citations": [...],
    "search_call_id": "ws_123456",
    "timestamp": "2025-01-27T10:30:00",
    "search_type": "stock_analysis"
  }
}
```

### 4. Market Alerts
```http
GET /api/web-search/market-alerts?type=breaking_news
```

**Response:**
```json
{
  "success": true,
  "alert_type": "breaking_news",
  "result": {
    "content": "Breaking market news...",
    "citations": [...],
    "search_call_id": "ws_123456",
    "timestamp": "2025-01-27T10:30:00",
    "search_type": "financial_news"
  }
}
```

### 5. Service Status
```http
GET /api/web-search/status
```

**Response:**
```json
{
  "available": true,
  "openai_configured": true,
  "search_types": [
    "market_data",
    "financial_news",
    "stock_analysis",
    "economic_indicators",
    "crypto_market",
    "forex_market",
    "commodities",
    "central_banks",
    "geopolitical"
  ],
  "cache_duration": 1800,
  "timestamp": "2025-01-27T10:30:00"
}
```

## Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for localization)
USER_COUNTRY=CH
USER_CITY=Genève
USER_REGION=Genève
```

### Dependencies
The implementation requires the following packages (already in your requirements.txt):
- `openai>=1.30.0`
- `requests>=2.32.0`
- `python-dotenv==1.0.0`

## Integration with Existing System

### Fallback Chain
The system implements a robust fallback mechanism:

1. **Primary**: Manus API (existing)
2. **Secondary**: OpenAI Web Search (new)
3. **Tertiary**: OpenAI Chat Completions (existing)

### Enhanced Market Briefing
The `generate_market_briefing()` function now includes web search as a fallback:

```python
def generate_market_briefing():
    """Génère un briefing de marché avec fallback vers web search OpenAI"""
    try:
        # 1. Essayer d'abord l'API Manus
        briefing = generate_market_briefing_manus()
        
        if briefing.get('status') == 'success':
            return briefing
        
        # 2. Fallback vers OpenAI Web Search
        if web_search_manager:
            briefing_content = web_search_manager.get_comprehensive_market_briefing()
            if briefing_content:
                return {
                    'status': 'success',
                    'briefing': {
                        'content': briefing_content,
                        'title': 'Briefing de Marché',
                        'summary': [],
                        'metrics': {}
                    },
                    'timestamp': datetime.now().isoformat(),
                    'source': 'OpenAI Web Search'
                }
        
        # 3. Fallback vers OpenAI Chat Completions
        if openai_client:
            briefing_content = generate_market_briefing_with_openai()
            if briefing_content:
                return {
                    'status': 'success',
                    'briefing': {
                        'content': briefing_content,
                        'title': 'Briefing de Marché',
                        'summary': [],
                        'metrics': {}
                    },
                    'timestamp': datetime.now().isoformat(),
                    'source': 'OpenAI Chat Completions'
                }
        
        return {'status': 'error', 'message': 'Aucune méthode disponible'}
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
```

## Usage Examples

### 1. Generate Market Briefing
```python
import requests

response = requests.post('http://localhost:5000/api/web-search/market-briefing', json={
    'user_location': {
        'country': 'CH',
        'city': 'Genève'
    },
    'search_context_size': 'high'
})

if response.status_code == 200:
    briefing = response.json()
    print(briefing['briefing'])
```

### 2. Search for Stock Information
```python
response = requests.get('http://localhost:5000/api/web-search/stock/AAPL')
if response.status_code == 200:
    stock_info = response.json()
    print(stock_info['result']['content'])
```

### 3. Get Market Alerts
```python
response = requests.get('http://localhost:5000/api/web-search/market-alerts?type=breaking_news')
if response.status_code == 200:
    alerts = response.json()
    print(alerts['result']['content'])
```

## Web Interface

### Access the Web Interface
Navigate to `http://localhost:5000/web-search` to access the interactive web interface.

### Features of the Web Interface
- **Real-time status checking** of the web search service
- **Market briefing generation** with location and context size options
- **Financial markets search** with multiple search types
- **Stock information lookup** with geographic localization
- **Market alerts** for breaking news
- **Citation display** with clickable links to sources
- **Responsive design** that works on desktop and mobile

## Testing

### Run the Test Script
```bash
python test_web_search_integration.py
```

This will test:
- Service status
- Market briefing generation
- Financial markets search
- Stock information search
- Market alerts
- Integration with existing endpoints

### Manual Testing
1. Start your Flask application
2. Navigate to `http://localhost:5000/web-search`
3. Test each section of the interface
4. Verify that citations are displayed and clickable
5. Check that location parameters are working

## Error Handling

### Common Error Scenarios
1. **OpenAI API Key Missing**
   - Error: "Web Search Manager non disponible"
   - Solution: Set `OPENAI_API_KEY` environment variable

2. **Network Issues**
   - Error: "Erreur de connexion"
   - Solution: Check internet connection and OpenAI API status

3. **Invalid Search Type**
   - Error: "Type de recherche invalide"
   - Solution: Use one of the valid search types

4. **Rate Limiting**
   - Error: OpenAI rate limit exceeded
   - Solution: Wait and retry, or upgrade API plan

### Logging
All web search operations are logged with appropriate levels:
- `INFO`: Successful operations
- `WARNING`: Configuration issues
- `ERROR`: API errors and exceptions

## Performance Considerations

### Caching
- Web search results are cached for 30 minutes by default
- Cache duration can be configured in `web_search_manager.py`

### Context Size Options
- **Low**: Fastest response, minimal context
- **Medium**: Balanced speed and completeness (default)
- **High**: Most comprehensive, slower response

### Rate Limiting
- OpenAI web search has the same rate limits as the underlying model
- Monitor usage to avoid hitting limits

## Security Considerations

### API Key Management
- Store `OPENAI_API_KEY` in environment variables
- Never commit API keys to version control
- Use `.env` file for local development

### Data Privacy
- Web search queries are sent to OpenAI
- No sensitive financial data is transmitted
- Citations are displayed but not stored

## Future Enhancements

### Planned Features
1. **Advanced Filtering** - Filter results by date, source, relevance
2. **Custom Search Templates** - Save and reuse search configurations
3. **Batch Processing** - Search multiple stocks simultaneously
4. **Historical Data** - Access historical market data
5. **Real-time Alerts** - WebSocket-based real-time notifications
6. **Export Functionality** - Export results to PDF, CSV, or Excel

### Integration Opportunities
1. **Email Notifications** - Send market alerts via email
2. **Dashboard Integration** - Add web search results to analytics dashboard
3. **Mobile App** - Create mobile interface for web search
4. **API Documentation** - Generate OpenAPI/Swagger documentation

## Troubleshooting

### Common Issues

1. **Module Import Error**
   ```
   ImportError: No module named 'web_search_manager'
   ```
   - Solution: Ensure `web_search_manager.py` is in the same directory as `app.py`

2. **OpenAI API Error**
   ```
   openai.AuthenticationError: Invalid API key
   ```
   - Solution: Verify your OpenAI API key is correct and has sufficient credits

3. **Web Search Not Available**
   ```
   "Web Search Manager non disponible"
   ```
   - Solution: Check that OpenAI client is properly initialized

4. **Template Not Found**
   ```
   jinja2.exceptions.TemplateNotFound: web_search.html
   ```
   - Solution: Ensure `web_search.html` is in the `templates/` directory

### Debug Mode
Enable debug logging by setting the log level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify your OpenAI API key and credits
3. Test with the provided test script
4. Use the web interface to isolate issues

## License

This implementation is part of your existing financial information system and follows the same licensing terms. 