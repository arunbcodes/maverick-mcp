# Company IR Mappings Guide

Complete guide to managing Company Investor Relations (IR) URL mappings in Maverick MCP.

## Overview

IR mappings tell Maverick MCP where to find earnings call transcripts on company websites. These mappings are stored in a database and can be managed through JSON seed files or direct database operations.

## Quick Start

### Seeding Pre-Configured Mappings

The system includes pre-configured IR mappings for top Indian companies:

```bash
# Docker
docker exec maverick-mcp-backend-1 python scripts/seed_concall_mappings.py

# Local (uv)
uv run python scripts/seed_concall_mappings.py
```

This will seed **10 Indian companies** including:
- RELIANCE.NS - Reliance Industries
- TCS.NS - Tata Consultancy Services
- INFY.NS - Infosys Limited
- HDFCBANK.NS - HDFC Bank
- ICICIBANK.NS - ICICI Bank
- WIPRO.NS - Wipro Limited
- BHARTIARTL.NS - Bharti Airtel
- ITC.NS - ITC Limited
- BAJFINANCE.NS - Bajaj Finance
- SBIN.NS - State Bank of India

## Understanding IR Mappings

### JSON Structure

IR mappings are defined in: `packages/india/src/maverick_india/concall/data/company_ir_seed.json`

```json
{
  "companies": [
    {
      "ticker": "RELIANCE.NS",
      "company_name": "Reliance Industries Limited",
      "ir_base_url": "https://www.ril.com/InvestorRelations.aspx",
      "concall_url_pattern": "https://www.ril.com/InvestorRelations/WebcastAndTranscript.aspx",
      "concall_section_xpath": "//div[contains(@class, 'transcript')]//a",
      "concall_section_css": "div.transcript a",
      "market": "NSE",
      "country": "IN",
      "is_active": true,
      "notes": "Most comprehensive IR. All transcripts as PDFs with audio.",
      "priority": 1
    }
  ]
}
```

### Field Descriptions

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `ticker` | ✅ Yes | Stock symbol with market suffix | `"RELIANCE.NS"`, `"AAPL"` |
| `company_name` | ✅ Yes | Full legal company name | `"Reliance Industries Limited"` |
| `ir_base_url` | ⚠️ Recommended | Base URL of IR section | `"https://www.ril.com/InvestorRelations.aspx"` |
| `concall_url_pattern` | ⚠️ Recommended | Direct URL to transcripts page | `"https://www.ril.com/.../Transcript.aspx"` |
| `concall_section_xpath` | ❌ Optional | XPath selector for transcript links | `"//div[@class='transcript']//a"` |
| `concall_section_css` | ❌ Optional | CSS selector (alternative to XPath) | `"div.transcript a"` |
| `market` | ✅ Yes | Stock exchange | `"NSE"`, `"NASDAQ"`, `"NYSE"` |
| `country` | ✅ Yes | Country code (ISO 3166-1 alpha-2) | `"IN"`, `"US"` |
| `is_active` | ✅ Yes | Whether actively tracked | `true`, `false` |
| `notes` | ❌ Optional | Manual notes about IR structure | Any text |
| `verification_status` | ❌ Auto | Status (active/broken/pending) | Auto-set |
| `last_verified` | ❌ Auto | Last verification timestamp | Auto-set |

## Adding New Companies

### Method 1: Edit JSON File (Recommended)

**Step 1:** Edit the seed file:

```bash
vim packages/india/src/maverick_india/concall/data/company_ir_seed.json
```

**Step 2:** Add your company:

```json
{
  "ticker": "TATAMOTORS.NS",
  "company_name": "Tata Motors Limited",
  "ir_base_url": "https://www.tatamotors.com/investors/",
  "concall_url_pattern": "https://www.tatamotors.com/investors/financials/quarterly-results/",
  "concall_section_xpath": "//div[@class='quarterly-results']//a",
  "market": "NSE",
  "country": "IN",
  "is_active": true,
  "notes": "Check Quarterly Results section for transcript PDFs"
}
```

**Step 3:** Run the seeder:

```bash
# Docker
docker exec maverick-mcp-backend-1 python scripts/seed_concall_mappings.py --update

# Local
uv run python scripts/seed_concall_mappings.py --update
```

The `--update` flag will update existing mappings if they already exist.

### Method 2: Direct Database Insert

```python
from maverick_india.concall.models import CompanyIRMapping
from maverick_data import SessionLocal
from datetime import datetime, UTC

session = SessionLocal()

try:
    mapping = CompanyIRMapping(
        ticker="TATAMOTORS.NS",
        company_name="Tata Motors Limited",
        ir_base_url="https://www.tatamotors.com/investors/",
        concall_url_pattern="https://www.tatamotors.com/investors/financials/quarterly-results/",
        market="NSE",
        country="IN",
        verification_status="pending",
        is_active=True,
        notes="Added manually for testing"
    )
    
    session.add(mapping)
    session.commit()
    print(f"✅ Added {mapping.ticker}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    session.rollback()
finally:
    session.close()
```

## Finding IR URLs

### Step-by-Step Process

**1. Visit Company Website**

Start with the company's main website (e.g., `www.reliance.com`)

**2. Navigate to Investor Relations**

Look for these sections:
- "Investor Relations"
- "Investors"
- "For Investors"
- "Shareholder Information"

Usually found in:
- Main navigation menu
- Footer links
- About section

**3. Find Earnings/Financial Results**

Within IR section, look for:
- "Financial Results"
- "Quarterly Results"
- "Earnings"
- "Reports & Filings"

**4. Locate Transcripts**

Common locations:
- Same page as quarterly results
- Separate "Transcripts" or "Webcast" section
- Under "Presentations & Transcripts"
- "Analyst Call Transcripts"

**5. Identify URL Patterns**

Check if transcripts follow a pattern:

```
✅ Good (Pattern-based):
https://www.company.com/ir/transcripts/Q1-2025-Transcript.pdf
https://www.company.com/downloads/results/FY2025/Q1/transcript.pdf

❌ Bad (No pattern):
https://www.company.com/getattachment/12345abcde/transcript.pdf
```

### Example: HDFC Bank

**Research Process:**

1. Visit: `https://www.hdfcbank.com`
2. Navigate: About Us → Investor Relations
3. Click: Financial Results
4. Find: "Transcript-Q2 FY26-Analyst Earnings Call.pdf"
5. Verify pattern across multiple quarters

**Result:**

```json
{
  "ticker": "HDFCBANK.NS",
  "company_name": "HDFC Bank Limited",
  "ir_base_url": "https://www.hdfcbank.com/personal/about-us/investor-relations",
  "concall_url_pattern": "https://www.hdfcbank.com/personal/about-us/investor-relations/financial-results",
  "concall_section_xpath": "//div[@class='financial-results']//a[contains(text(), 'Transcript')]",
  "market": "NSE",
  "country": "IN",
  "is_active": true,
  "notes": "Path: Financial Results > Select FY > Quarter > 'Transcript-Q2 FY26-Analyst Earnings Call'"
}
```

## XPath and CSS Selectors

### When to Use Selectors

Use XPath/CSS selectors when:
- Transcripts are listed on a dynamic page
- URLs don't follow a predictable pattern
- Need to scrape links from quarterly results page

### Common XPath Patterns

```xpath
# Find all links in a transcript section
//div[contains(@class, 'transcript')]//a

# Find links with "transcript" in text
//a[contains(text(), 'Transcript')]

# Find links in specific section by ID
//div[@id='quarterly-results']//a

# Find PDF links only
//a[contains(@href, '.pdf')]

# Complex: Transcript links in Q1 FY2025 section
//div[contains(text(), 'Q1 FY2025')]//following-sibling::div//a[contains(text(), 'Transcript')]
```

### Common CSS Selectors

```css
/* All links in transcript section */
div.transcript a

/* Links with specific class */
a.transcript-link

/* Links in results section */
#quarterly-results a

/* PDF links */
a[href$='.pdf']

/* Specific text content */
a:contains('Transcript')
```

### Testing Selectors

**In Browser Console:**

```javascript
// Test XPath
$x("//div[contains(@class, 'transcript')]//a")

// Test CSS
$$("div.transcript a")
```

**In Python:**

```python
from bs4 import BeautifulSoup

# Test CSS selector
soup = BeautifulSoup(html_content, 'html.parser')
links = soup.select("div.transcript a")

# Test with lxml (XPath)
from lxml import html
tree = html.fromstring(html_content)
links = tree.xpath("//div[contains(@class, 'transcript')]//a")
```

## Seeding Script Commands

### Basic Commands

```bash
# Seed default mappings
python scripts/seed_concall_mappings.py

# Seed from custom file
python scripts/seed_concall_mappings.py --file /path/to/custom.json

# Update existing mappings (overwrite)
python scripts/seed_concall_mappings.py --update

# Verify data after seeding
python scripts/seed_concall_mappings.py --verify

# List seeded mappings
python scripts/seed_concall_mappings.py --list 20
```

### Docker Commands

```bash
# Seed in Docker container
docker exec maverick-mcp-backend-1 python scripts/seed_concall_mappings.py

# Seed with custom file (mount volume first)
docker cp custom_ir.json maverick-mcp-backend-1:/tmp/
docker exec maverick-mcp-backend-1 python scripts/seed_concall_mappings.py --file /tmp/custom_ir.json

# Update and verify
docker exec maverick-mcp-backend-1 python scripts/seed_concall_mappings.py --update --verify

# List all mappings
docker exec maverick-mcp-backend-1 python scripts/seed_concall_mappings.py --list 50
```

## Verification and Testing

### Verify Seeded Data

```bash
python scripts/seed_concall_mappings.py --verify
```

**Output:**
```
Total mappings: 10
Active: 10, Inactive: 0
By market: {'NSE': 10}
By country: {'IN': 10}
```

### Test Transcript Fetching

```python
from maverick_india.concall import TranscriptFetcher
import asyncio

async def test():
    fetcher = TranscriptFetcher(save_to_db=True)
    result = await fetcher.fetch_transcript(
        ticker="RELIANCE.NS",
        quarter="Q2",
        fiscal_year=2025
    )
    return result

result = asyncio.run(test())
print(result)
```

### Check Database

```python
from maverick_india.concall.models import CompanyIRMapping
from maverick_data import SessionLocal

session = SessionLocal()

# Count total mappings
total = session.query(CompanyIRMapping).count()
print(f"Total mappings: {total}")

# List all tickers
mappings = session.query(CompanyIRMapping).all()
for m in mappings:
    print(f"{m.ticker}: {m.company_name} ({m.verification_status})")

session.close()
```

## URL Patterns and Templates

### Pattern Syntax

IR mappings support simple URL templates:

```
Original pattern in JSON:
https://www.company.com/ir/transcripts/{quarter}_{year}_Transcript.pdf

Will be formatted as:
https://www.company.com/ir/transcripts/Q1_2025_Transcript.pdf
```

### Common Pattern Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{quarter}` | Quarter (Q1, Q2, Q3, Q4) | `Q1` |
| `{year}` | Fiscal year (4 digits) | `2025` |
| `{fiscal_year}` | Same as year | `2025` |
| `{fy}` | Short fiscal year (2 digits) | `25` |

**Note:** Current implementation may need enhancement for complex patterns. For now, use `concall_url_pattern` to point to the transcript listing page and let the scraper find links.

## Best Practices

### ✅ Do's

1. **Always verify URLs manually first**
   - Visit the IR page yourself
   - Download a transcript to confirm access
   - Check multiple quarters to identify patterns

2. **Include detailed notes**
   ```json
   "notes": "Transcripts under Financial Results > FY2025 > Q1 > 'Analyst Call Transcript.pdf'. Structure may change yearly."
   ```

3. **Set appropriate verification status**
   - `"active"` - Tested and working
   - `"pending"` - Not yet verified
   - `"broken"` - Known to be broken

4. **Use descriptive selectors**
   ```json
   "concall_section_xpath": "//div[@id='quarterly-results']//a[contains(@href, 'transcript')]"
   ```

5. **Test before committing**
   ```bash
   python scripts/seed_concall_mappings.py --file test.json --verify
   ```

### ❌ Don'ts

1. **Don't add unverified mappings**
   - Always test URLs before adding

2. **Don't use generic patterns**
   ```json
   ❌ "concall_url_pattern": "https://www.company.com/"
   ✅ "concall_url_pattern": "https://www.company.com/investors/earnings-calls"
   ```

3. **Don't forget market suffix**
   ```json
   ❌ "ticker": "RELIANCE"
   ✅ "ticker": "RELIANCE.NS"
   ```

4. **Don't mix markets**
   ```json
   ❌ "market": "NSE", "country": "US"
   ✅ "market": "NSE", "country": "IN"
   ```

5. **Don't leave empty required fields**
   ```json
   ❌ "company_name": "",
   ✅ "company_name": "Reliance Industries Limited",
   ```

## Troubleshooting

### Mapping Not Working

**Symptom:** Transcript fetch fails even with mapping

**Check:**
1. Verify URL is accessible
   ```bash
   curl -I https://www.ril.com/InvestorRelations.aspx
   ```

2. Test XPath/CSS selector
   ```python
   from lxml import html
   import requests
   
   response = requests.get("https://www.company.com/ir")
   tree = html.fromstring(response.content)
   links = tree.xpath("//div[@class='transcript']//a")
   print(f"Found {len(links)} links")
   ```

3. Check database
   ```python
   from maverick_india.concall.models import CompanyIRMapping
   from maverick_data import SessionLocal
   
   session = SessionLocal()
   mapping = session.query(CompanyIRMapping).filter_by(ticker="RELIANCE.NS").first()
   print(f"Mapping exists: {mapping is not None}")
   print(f"Status: {mapping.verification_status if mapping else 'N/A'}")
   ```

### Seeding Fails

**Common Errors:**

**1. Invalid JSON**
```
Error: Invalid JSON in company_ir_seed.json: Expecting ',' delimiter
```
**Fix:** Validate JSON syntax at jsonlint.com

**2. Missing Required Field**
```
Error: Failed to seed TATAMOTORS.NS: KeyError: 'ticker'
```
**Fix:** Ensure all required fields are present

**3. Duplicate Ticker**
```
Skipping existing mapping for RELIANCE.NS
```
**Fix:** Use `--update` flag to overwrite

### Verification Fails

```bash
python scripts/seed_concall_mappings.py --verify
# Output: Total mappings: 0
```

**Possible Causes:**
- Database not initialized
- Wrong database URL
- Migration not run

**Fix:**
```bash
# Run migrations
alembic upgrade head

# Check database connection
python -c "from maverick_data import SessionLocal; from maverick_india.concall.models import CompanyIRMapping; s = SessionLocal(); print(s.query(CompanyIRMapping).count())"
```

## Market-Specific Guidance

### Indian Companies (NSE/BSE)

**Characteristics:**
- Usually have dedicated IR sections
- Quarterly results with presentations
- Transcripts may be separate PDFs
- Some use third-party IR platforms

**Best Sources:**
- Company website first
- NSE announcements as fallback
- BSE filings (alternative)

**Example: IT Companies**
- TCS, Infosys, Wipro: Excellent IR pages
- Well-organized quarterly results
- Separate transcript and presentation downloads

**Example: Banks**
- HDFC, ICICI, SBI: Good IR sections
- May require navigating through year/quarter dropdowns
- Transcripts often in "Investor Downloads" section

### US Companies (NYSE/NASDAQ)

**Characteristics:**
- Professional IR platforms (e.g., IRW)
- Usually have searchable archives
- May use services like Seeking Alpha
- Transcripts in "Events & Presentations"

**Best Sources:**
- Company IR website
- SEC Edgar filings (8-K exhibits)
- Third-party platforms (Seeking Alpha, Motley Fool)

## API Reference

For programmatic access to IR mappings:

```python
from maverick_india.concall.models import CompanyIRMapping
from maverick_data import SessionLocal

# Query mappings
session = SessionLocal()

# Get specific company
mapping = session.query(CompanyIRMapping).filter_by(ticker="RELIANCE.NS").first()

# Get all active Indian companies
indian_companies = session.query(CompanyIRMapping).filter(
    CompanyIRMapping.country == "IN",
    CompanyIRMapping.is_active == True
).all()

# Get companies needing verification
needs_verification = session.query(CompanyIRMapping).filter(
    CompanyIRMapping.verification_status.in_(["pending", "broken"])
).all()
```

## Contributing

### Adding Bulk Mappings

If you have many mappings to add:

1. Create a JSON file with all mappings
2. Validate JSON structure
3. Test with a small batch first
4. Run with full file

```bash
# Test with first 3 companies
jq '.companies |= .[:3]' full_mappings.json > test_mappings.json
python scripts/seed_concall_mappings.py --file test_mappings.json --verify

# If successful, seed full file
python scripts/seed_concall_mappings.py --file full_mappings.json --verify
```

### Submitting New Mappings

To contribute mappings back to the project:

1. Add to `packages/india/src/maverick_india/concall/data/company_ir_seed.json`
2. Test thoroughly
3. Add notes about IR structure
4. Create pull request with verification results

## Next Steps

- [Fetching Transcripts →](fetching-transcripts.md)
- [Transcript Providers →](../api-reference/concall/providers.md)
- [Database Schema →](database-schema.md)

---

**Last Updated:** 2025-11-16
**Maintained By:** Maverick MCP Team

