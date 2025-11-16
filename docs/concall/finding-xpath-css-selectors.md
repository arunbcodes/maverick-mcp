# Finding XPath and CSS Selectors for IR Mappings

Complete visual guide to finding XPath and CSS selectors for company IR websites.

## Why Do We Need Selectors?

When adding companies to the IR mapping database, you need to tell the system **where** to find transcript links on their IR webpage. This is done using:

- **XPath**: XML Path Language for navigating HTML structure
- **CSS Selectors**: Same selectors used in CSS stylesheets

These selectors act like "instructions" to find specific elements on a webpage.

## Quick Start - Browser DevTools

All modern browsers have built-in tools for inspecting web pages and finding selectors.

### Chrome/Edge DevTools

**Step 1: Open DevTools**
- Right-click on the page → "Inspect" 
- Or press `F12`
- Or press `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Opt+I` (Mac)

**Step 2: Enable Selector Mode**
- Click the "Select element" icon (top-left of DevTools)
- Or press `Ctrl+Shift+C` (Windows/Linux) or `Cmd+Shift+C` (Mac)

**Step 3: Click on Element**
- Hover over the transcript link on the webpage
- Click when the link is highlighted
- DevTools will show you the exact HTML element

### Firefox DevTools

Same process as Chrome, with similar keyboard shortcuts.

### Safari Web Inspector

**Enable Developer Tools First:**
1. Safari → Settings → Advanced
2. Check "Show Develop menu in menu bar"

**Then:**
- Develop → Show Web Inspector
- Or `Cmd+Opt+I`

## Real-World Example: Finding Reliance IR Selectors

Let's walk through finding selectors for **Reliance Industries Limited**.

### Step 1: Navigate to IR Page

Visit: `https://www.ril.com/InvestorRelations/WebcastAndTranscript.aspx`

### Step 2: Locate Transcript Section

Look for the section containing transcript links. Usually:
- Under "Quarterly Results"
- In "Transcripts" or "Earnings Calls" section
- Near "Webcast & Transcripts"

For Reliance, there's a clear section with transcript PDFs.

### Step 3: Inspect a Transcript Link

**Right-click on a transcript link** → "Inspect"

You'll see HTML like:
```html
<div class="transcript-section">
  <div class="quarter-results">
    <h3>Q1 FY 2025</h3>
    <a href="/downloads/Q1-FY2025-Transcript.pdf" target="_blank">
      Download Transcript (PDF)
    </a>
  </div>
</div>
```

### Step 4: Write the CSS Selector

**Goal**: Find ALL transcript links in this section

**Option 1 - By Class:**
```css
.transcript-section a
```
This finds all `<a>` tags inside elements with class `transcript-section`

**Option 2 - More Specific:**
```css
.transcript-section .quarter-results a
```

**Option 3 - By Attribute:**
```css
a[href*="Transcript.pdf"]
```
This finds all links where `href` contains "Transcript.pdf"

### Step 5: Write the XPath

**Same goal, using XPath syntax:**

**Option 1 - By Class:**
```xpath
//div[contains(@class, 'transcript-section')]//a
```

**Option 2 - By Text Content:**
```xpath
//a[contains(text(), 'Transcript')]
```

**Option 3 - By href Attribute:**
```xpath
//a[contains(@href, 'Transcript.pdf')]
```

### Step 6: Test Your Selector

**In Chrome Console (F12 → Console):**

```javascript
// Test CSS Selector
document.querySelectorAll('.transcript-section a')
// Should return: NodeList of links

// Test XPath
document.evaluate(
  "//div[contains(@class, 'transcript-section')]//a",
  document,
  null,
  XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
  null
)
// Or use Chrome's shortcut:
$x("//div[contains(@class, 'transcript-section')]//a")
```

**Expected Result:**
```javascript
// Should return 4-8 links (depending on quarters available)
NodeList(6) [
  <a href="/downloads/Q1-FY2025-Transcript.pdf">...</a>,
  <a href="/downloads/Q4-FY2024-Transcript.pdf">...</a>,
  ...
]
```

If you get **0 results**, your selector is wrong. Try again!

## Common HTML Patterns on IR Pages

### Pattern 1: Simple List of Links

```html
<div id="transcripts">
  <ul>
    <li><a href="Q1-2025.pdf">Q1 FY2025 Transcript</a></li>
    <li><a href="Q4-2024.pdf">Q4 FY2024 Transcript</a></li>
  </ul>
</div>
```

**CSS Selector:**
```css
#transcripts a
```

**XPath:**
```xpath
//div[@id='transcripts']//a
```

### Pattern 2: Table with Transcripts

```html
<table class="financial-results">
  <tr>
    <td>Q1 FY2025</td>
    <td><a href="transcript-q1-2025.pdf">Download</a></td>
  </tr>
  <tr>
    <td>Q4 FY2024</td>
    <td><a href="transcript-q4-2024.pdf">Download</a></td>
  </tr>
</table>
```

**CSS Selector:**
```css
table.financial-results a
```

**XPath:**
```xpath
//table[contains(@class, 'financial-results')]//a
```

### Pattern 3: Accordion/Expandable Section

```html
<div class="accordion">
  <div class="accordion-item">
    <h4 class="accordion-header">Q1 FY2025</h4>
    <div class="accordion-body">
      <a href="transcript.pdf">Transcript</a>
      <a href="presentation.pdf">Presentation</a>
    </div>
  </div>
</div>
```

**CSS Selector (Only Transcript Links):**
```css
.accordion-body a[href*="transcript"]
```

**XPath:**
```xpath
//div[contains(@class, 'accordion-body')]//a[contains(@href, 'transcript')]
```

### Pattern 4: Links with Specific Text

```html
<div class="documents">
  <a href="doc1.pdf">Financial Results</a>
  <a href="doc2.pdf">Earnings Call Transcript</a>
  <a href="doc3.pdf">Investor Presentation</a>
</div>
```

**CSS Selector (Text-based):**
```css
/* CSS doesn't support text-based selection well */
/* Use XPath instead */
```

**XPath:**
```xpath
//div[@class='documents']//a[contains(text(), 'Transcript')]
```

## XPath Syntax Cheatsheet

### Basic Structure

```xpath
//tagname[@attribute='value']
```

- `//` = Search anywhere in document
- `tagname` = HTML tag (div, a, span, etc.)
- `@attribute` = HTML attribute (class, id, href, etc.)
- `'value'` = Exact value to match

### Common XPath Patterns

| Pattern | Syntax | Example |
|---------|--------|---------|
| **Any tag with class** | `//tag[@class='name']` | `//div[@class='transcript']` |
| **Class contains** | `//tag[contains(@class, 'name')]` | `//div[contains(@class, 'transcript')]` |
| **Any descendant** | `//parent//child` | `//div[@id='ir']//a` |
| **Text contains** | `//tag[contains(text(), 'word')]` | `//a[contains(text(), 'Transcript')]` |
| **Attribute contains** | `//tag[contains(@attr, 'val')]` | `//a[contains(@href, '.pdf')]` |
| **Multiple conditions** | `//tag[@a='x' and @b='y']` | `//a[@class='link' and contains(@href, 'pdf')]` |
| **Following sibling** | `//tag/following-sibling::tag` | `//h3[text()='Q1']/following-sibling::a` |

### Advanced XPath Examples

**Find links after a specific heading:**
```xpath
//h3[contains(text(), 'Q1 FY2025')]/following-sibling::div//a
```

**Find PDF links only:**
```xpath
//a[contains(@href, '.pdf')]
```

**Find links in a specific section:**
```xpath
//section[@id='quarterly-results']//a[contains(text(), 'Transcript')]
```

**Find links with specific classes:**
```xpath
//a[contains(@class, 'transcript-link') or contains(@class, 'download-link')]
```

## CSS Selector Cheatsheet

### Basic Structure

```css
tag.class#id[attribute]
```

### Common CSS Patterns

| Pattern | Syntax | Example |
|---------|--------|---------|
| **Class selector** | `.classname` | `.transcript` |
| **ID selector** | `#idname` | `#quarterly-results` |
| **Descendant** | `parent child` | `div.ir a` |
| **Direct child** | `parent > child` | `div.ir > a` |
| **Attribute equals** | `[attr='value']` | `[href='transcript.pdf']` |
| **Attribute contains** | `[attr*='value']` | `[href*='transcript']` |
| **Attribute starts with** | `[attr^='value']` | `[href^='/downloads']` |
| **Attribute ends with** | `[attr$='value']` | `[href$='.pdf']` |
| **Multiple classes** | `.class1.class2` | `.transcript.download` |

### Advanced CSS Examples

**Links inside transcript section:**
```css
div.transcript-section a
```

**PDF links only:**
```css
a[href$='.pdf']
```

**Links with specific class:**
```css
a.transcript-link, a.download-link
```

**Nested structure:**
```css
#investor-relations .quarterly-results .transcripts a
```

## Testing Your Selectors in Browser

### Method 1: Chrome Console

**For CSS:**
```javascript
// Get all matching elements
document.querySelectorAll('your-css-selector')

// Get first matching element
document.querySelector('your-css-selector')

// Count matches
document.querySelectorAll('.transcript a').length

// Chrome shortcut (same as querySelectorAll)
$$('.transcript a')
```

**For XPath:**
```javascript
// Chrome's built-in XPath helper
$x("//div[@class='transcript']//a")

// Full XPath evaluation
document.evaluate(
  "//div[@class='transcript']//a",
  document,
  null,
  XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
  null
)
```

### Method 2: Copy Selector from DevTools

**Chrome:**
1. Inspect element (right-click → Inspect)
2. In Elements panel, right-click the highlighted element
3. Copy → Copy selector (CSS) or Copy XPath

**Result:**
```
CSS: body > div#content > div.ir-section > a:nth-child(3)
XPath: /html/body/div[2]/div[1]/a[3]
```

⚠️ **Warning**: Auto-generated selectors are often brittle and break easily. Hand-crafted selectors are more reliable!

### Method 3: Browser Extensions

**Chrome/Edge:**
- **ChroPath**: Free XPath/CSS selector generator
- **SelectorsHub**: Advanced selector testing
- **XPath Helper**: Hover and get XPath

**Firefox:**
- **XPath Finder**: Similar to Chrome extensions
- **CSS Selector Finder**: Built into DevTools

## Real-World Examples from JSON

### Example 1: HDFC Bank

**Website Structure:**
```html
<div class="financial-results">
  <select id="year">...</select>
  <select id="quarter">...</select>
  <div class="results-content">
    <a href="/downloads/Q1-FY2025-Transcript.pdf">
      Transcript-Q1 FY25-Analyst Earnings Call
    </a>
  </div>
</div>
```

**Selectors in JSON:**
```json
{
  "ticker": "HDFCBANK.NS",
  "concall_section_xpath": "//div[@class='financial-results']//a[contains(text(), 'Transcript')]",
  "concall_section_css": ".financial-results a:contains('Transcript')"
}
```

### Example 2: TCS

**Website Structure:**
```html
<div id="quarterly-results">
  <h3>Q1 FY2025 Results</h3>
  <div class="downloads">
    <a href="/ir/q1-transcript.pdf" class="transcript-link">Transcript</a>
    <a href="/ir/q1-ppt.pdf" class="ppt-link">Presentation</a>
  </div>
</div>
```

**Selectors in JSON:**
```json
{
  "ticker": "TCS.NS",
  "concall_section_xpath": "//div[@id='quarterly-results']//a",
  "concall_section_css": "#quarterly-results a"
}
```

### Example 3: Reliance (Complex)

**Website Structure:**
```html
<div class="investor-relations">
  <div class="tabs">
    <div class="tab-content active" id="transcripts">
      <table class="transcript-table">
        <tr>
          <td class="quarter">Q1 FY2025</td>
          <td class="date">July 19, 2024</td>
          <td class="download">
            <a href="https://www.ril.com/.../Q1-FY25-Transcript.pdf" target="_blank">
              <i class="icon-download"></i> Download
            </a>
          </td>
        </tr>
      </table>
    </div>
  </div>
</div>
```

**Selectors in JSON:**
```json
{
  "ticker": "RELIANCE.NS",
  "concall_section_xpath": "//div[contains(@class, 'transcript')]//a",
  "concall_section_css": "div.transcript a, table.transcript-table a"
}
```

## Step-by-Step Walkthrough

Let's add **Tata Motors** as a complete example.

### Step 1: Visit IR Page

Navigate to: `https://www.tatamotors.com/investors/`

### Step 2: Find Quarterly Results

Click through:
1. "Investors" → "Financials"
2. "Quarterly Results"
3. Look for latest quarter

### Step 3: Identify Transcript Pattern

You see:
```
Q1 FY 2025 Results
├── Financial Results (PDF)
├── Analyst Presentation (PDF)
└── Earnings Call Transcript (PDF) ← This is what we want!
```

### Step 4: Inspect the Link

Right-click "Earnings Call Transcript" → Inspect

```html
<div class="quarterly-results">
  <div class="result-item">
    <h4>Q1 FY 2025</h4>
    <ul class="documents">
      <li><a href="/docs/results.pdf">Financial Results</a></li>
      <li><a href="/docs/presentation.pdf">Analyst Presentation</a></li>
      <li><a href="/docs/transcript.pdf" class="transcript">
        Earnings Call Transcript
      </a></li>
    </ul>
  </div>
</div>
```

### Step 5: Write Selectors

**CSS (Option 1 - By class):**
```css
.quarterly-results a.transcript
```

**CSS (Option 2 - By text in link):**
```css
.documents a[href*="transcript"]
```

**XPath (Option 1 - By class):**
```xpath
//div[contains(@class, 'quarterly-results')]//a[contains(@class, 'transcript')]
```

**XPath (Option 2 - By text):**
```xpath
//div[@class='documents']//a[contains(text(), 'Transcript')]
```

### Step 6: Test in Console

```javascript
// Test CSS
$$('.quarterly-results a.transcript')
// Result: NodeList(4) - Found 4 quarters!

// Test XPath
$x("//div[contains(@class, 'quarterly-results')]//a[contains(@class, 'transcript')]")
// Result: Array(4) - Success!
```

### Step 7: Add to JSON

```json
{
  "ticker": "TATAMOTORS.NS",
  "company_name": "Tata Motors Limited",
  "ir_base_url": "https://www.tatamotors.com/investors/",
  "concall_url_pattern": "https://www.tatamotors.com/investors/financials/quarterly-results/",
  "concall_section_xpath": "//div[contains(@class, 'quarterly-results')]//a[contains(@class, 'transcript')]",
  "concall_section_css": ".quarterly-results a.transcript",
  "market": "NSE",
  "country": "IN",
  "is_active": true,
  "notes": "Transcripts in Financials → Quarterly Results → Look for 'Earnings Call Transcript' link"
}
```

## Troubleshooting

### Selector Returns Nothing

**Problem:** `$x("//div[@class='transcript']//a")` returns `[]`

**Solutions:**

1. **Check if class exists:**
   ```javascript
   $$('div')  // See all divs
   // Look through results for your section
   ```

2. **Try broader selector:**
   ```javascript
   // Instead of exact match
   $x("//div[@class='transcript-section']//a")
   // Try contains
   $x("//div[contains(@class, 'transcript')]//a")
   ```

3. **Check if content is dynamic (JavaScript-loaded):**
   ```javascript
   // Wait for page to fully load
   setTimeout(() => {
     $x("//div[@class='transcript']//a")
   }, 3000)
   ```

4. **Check if inside iframe:**
   ```javascript
   // Switch to iframe first
   const iframe = document.querySelector('iframe')
   const iframeDoc = iframe.contentDocument
   iframeDoc.querySelectorAll('.transcript a')
   ```

### Selector Too Specific (Breaks Easily)

**Problem:** Selector works now but breaks after website update

**Bad (Brittle):**
```css
body > div:nth-child(3) > div:nth-child(2) > a:nth-child(5)
```

**Good (Flexible):**
```css
.investor-relations .transcripts a
```

**Best Practice:**
- Use semantic classes/IDs
- Avoid positional selectors (`:nth-child`)
- Test across multiple quarters
- Use `contains()` for partial matches

### Multiple Selectors Return Different Results

**Problem:** CSS and XPath return different elements

**Debug:**
```javascript
const cssResults = $$('.transcript a')
const xpathResults = $x("//div[@class='transcript']//a")

console.log('CSS:', cssResults.length)
console.log('XPath:', xpathResults.length)

// Compare first elements
console.log('CSS first:', cssResults[0])
console.log('XPath first:', xpathResults[0])
```

**Solution:**
- Pick the one that returns ALL transcript links
- Test across multiple pages
- Choose simpler, more maintainable selector

## Best Practices

### ✅ Do's

1. **Test across multiple quarters**
   ```javascript
   // Navigate to different quarters and test
   $x("//div[@class='transcripts']//a")
   // Should work on Q1, Q2, Q3, Q4 pages
   ```

2. **Use semantic selectors**
   ```css
   /* Good - uses meaningful class */
   .transcripts a
   
   /* Bad - uses generated class */
   .jsx-12345678 a
   ```

3. **Prefer classes over IDs (if IDs change)**
   ```css
   /* IDs might be dynamic */
   #result-123456 a
   
   /* Classes are usually stable */
   .quarterly-results a
   ```

4. **Include backup selector**
   ```json
   "concall_section_xpath": "//div[@id='transcripts']//a",
   "concall_section_css": "#transcripts a, .transcript-section a"
   ```

5. **Add detailed notes**
   ```json
   "notes": "Transcripts under 'Investors' → 'Quarterly Results'. Links have class 'transcript-download'. Structure stable since 2023."
   ```

### ❌ Don'ts

1. **Don't use auto-generated selectors**
   ```css
   /* Chrome's Copy Selector gives this - DON'T USE */
   body > div:nth-child(4) > main > section:nth-child(2) > div > a:nth-child(3)
   ```

2. **Don't rely on exact text matches**
   ```xpath
   /* Breaks if text changes slightly */
   //a[text()='Download Q1 FY2025 Transcript']
   
   /* Better - partial match */
   //a[contains(text(), 'Transcript')]
   ```

3. **Don't forget to handle edge cases**
   - What if no transcripts are published?
   - What if structure is different for old quarters?
   - What if links are inside a dropdown?

## Tools & Resources

### Browser Extensions

**Chrome/Edge:**
- [ChroPath](https://chrome.google.com/webstore/detail/chropath/) - Best XPath generator
- [SelectorsHub](https://chrome.google.com/webstore/detail/selectorshub/) - Advanced testing
- [XPath Helper](https://chrome.google.com/webstore/detail/xpath-helper/) - Simple hover tool

**Firefox:**
- [XPath Finder](https://addons.mozilla.org/en-US/firefox/addon/xpath-finder/) - Similar to ChroPath
- Built-in DevTools have excellent CSS/XPath support

### Online Tools

- [XPath Tester](https://www.freeformatter.com/xpath-tester.html) - Test XPath online
- [CSS Selector Tester](https://www.w3schools.com/cssref/trysel.asp) - Test CSS selectors
- [Regex101](https://regex101.com/) - For complex attribute matching

### Learning Resources

- [XPath Tutorial (W3Schools)](https://www.w3schools.com/xml/xpath_intro.asp)
- [CSS Selectors Reference (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors)
- [Chrome DevTools Guide](https://developer.chrome.com/docs/devtools/)

## Quick Reference Card

### Most Common Patterns

```javascript
// 1. Find all links in a section
$x("//div[@id='transcripts']//a")
$$('#transcripts a')

// 2. Find links containing "transcript"
$x("//a[contains(text(), 'Transcript')]")
$$('a')  // Then filter manually

// 3. Find PDF links
$x("//a[contains(@href, '.pdf')]")
$$('a[href$=".pdf"]')

// 4. Find links with specific class
$x("//a[contains(@class, 'transcript')]")
$$('a.transcript, a.transcript-link')

// 5. Find links in table
$x("//table[@class='results']//a")
$$('table.results a')
```

## Next Steps

- [IR Mappings Guide →](ir-mappings-guide.md) - Add your selectors to JSON
- [Fetching Transcripts →](fetching-transcripts.md) - Test your mappings
- [Database Schema →](database-schema.md) - Understanding the data model

---

**Pro Tip:** The best way to learn is by practicing! Open your favorite company's IR page and try finding selectors yourself.

**Last Updated:** 2025-11-16

