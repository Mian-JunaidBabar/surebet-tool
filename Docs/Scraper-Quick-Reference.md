# Scraper Quick Reference

## Quick Start

### Test a URL without database saves

```bash
curl -X POST http://localhost:8000/api/v1/scraper/test-target \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.betexplorer.com/football/",
    "strategy": "betexplorer"
  }' | jq
```

### Find correct selectors visually

```bash
# Enter container
docker compose exec scraper bash

# Launch visual selector tool
playwright codegen https://www.betexplorer.com/football/
```

### Debug step-by-step

```bash
# Inside container
PWDEBUG=1 python scraper.py
```

## Supported Strategies

| Strategy      | Sites           | Status                     |
| ------------- | --------------- | -------------------------- |
| `betexplorer` | betexplorer.com | ✅ Hardened with fallbacks |
| `oddschecker` | oddschecker.com | ✅ Role-based selectors    |
| `oddsportal`  | oddsportal.com  | ⚠️ Basic (can be enhanced) |

## Test Endpoints

### Backend (Port 8000)

```bash
POST /api/v1/scraper/test-target
{
    "url": "https://www.betexplorer.com/football/",
    "strategy": "betexplorer"
}
```

### Scraper (Port 8001)

```bash
POST /test-scrape
{
    "url": "https://www.betexplorer.com/football/",
    "strategy": "betexplorer"
}
```

## Common Commands

```bash
# Rebuild containers
docker compose down && docker compose up --build -d

# View logs
docker compose logs scraper -f

# Enter scraper container
docker compose exec scraper bash

# Test BetExplorer
curl -X POST http://localhost:8000/api/v1/scraper/test-target \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.betexplorer.com/football/", "strategy": "betexplorer"}' | jq

# Test Oddschecker
curl -X POST http://localhost:8000/api/v1/scraper/test-target \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.oddschecker.com/football", "strategy": "oddschecker"}' | jq

# Check API health
curl http://localhost:8000/health | jq
curl http://localhost:8001/health | jq
```

## Debugging Workflow

1. **Find selectors**: `playwright codegen <URL>`
2. **Test quickly**: `curl POST /api/v1/scraper/test-target`
3. **Debug deeply**: `PWDEBUG=1 python scraper.py`
4. **Check logs**: `docker compose logs scraper -f`

## Selector Priority

1. Role-based: `page.get_by_role("link")`
2. Data attributes: `[data-odds]`
3. Semantic HTML: `main`, `nav`
4. Functional IDs: `#sports-navigation`
5. CSS classes: `.event-row` (least reliable)

## Response Format

```json
{
  "success": true,
  "message": "Successfully scraped 10 events",
  "count": 10,
  "timestamp": "2025-01-22 10:30:00",
  "events": [
    {
      "event_name": "Man Utd vs Chelsea",
      "odds": [2.5, 3.1, 2.8],
      "deep_link": "https://...",
      "source": "BetExplorer",
      "scraped_at": "2025-01-22 10:30:00"
    }
  ]
}
```
