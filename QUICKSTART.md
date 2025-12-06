# Quick Start Examples

> **Note**: 
> - All `python` commands work on Linux, Mac, Windows Command Prompt, and PowerShell.
> - On Windows, you can use `py` instead of `python` (e.g., `py discover_feeds.py websites.json`).

## 📂 Before You Start: File Location

**Important**: Make sure you're in the project directory when running commands!

```bash
# Navigate to the project folder first
cd path/to/url-to-feed

# Now you can run the examples below
```

**Alternative**: If you're in a different directory, use full paths:
```bash
python C:\path\to\url-to-feed\discover_feeds.py C:\path\to\websites.json
```

---

## Example 1: Basic Usage
```bash
python discover_feeds.py websites.json
# Windows alternative: py discover_feeds.py websites.json
```

## Example 2: Custom Output File
```bash
python discover_feeds.py websites.json -o my_feeds.json
# Windows alternative: py discover_feeds.py websites.json -o my_feeds.json
```

## Example 3: Process CSV File
```bash
python discover_feeds.py sites.csv -o feeds_output.json
# Windows alternative: py discover_feeds.py sites.csv -o feeds_output.json
```

## Example 4: Faster Processing (More Workers)
```bash
python discover_feeds.py websites.json -w 16
# Windows alternative: py discover_feeds.py websites.json -w 16
```

## Example 5: Slower, More Polite Crawling
```bash
python discover_feeds.py websites.json --delay 0.5 --timeout 15
# Windows alternative: py discover_feeds.py websites.json --delay 0.5 --timeout 15
```

## Example 6: Create Your Input File

You have two template options:

### Option A: Simple (URLs only) - Recommended for quick start

**Linux/Mac (bash):**
```bash
cp websites.simple.example.json websites.json
```

**Windows (Command Prompt):**
```cmd
copy websites.simple.example.json websites.json
```

**Windows (PowerShell):**
```powershell
Copy-Item websites.simple.example.json websites.json
```

Then edit `websites.json` - just add your URLs:
```json
[
  "https://techcrunch.com",
  "https://arstechnica.com",
  "https://www.theverge.com"
]
```

### Option B: With metadata (name and category)

**Linux/Mac (bash):**
```bash
cp websites.example.json websites.json
```

**Windows (Command Prompt):**
```cmd
copy websites.example.json websites.json
```

**Windows (PowerShell):**
```powershell
Copy-Item websites.example.json websites.json
```

Then edit `websites.json` with your sites:
```json
{
  "websites": [
    { "url": "https://techcrunch.com", "name": "TechCrunch", "category": "Tech News" },
    { "url": "https://arstechnica.com", "name": "Ars Technica", "category": "Tech" },
    { "url": "https://www.theverge.com", "name": "The Verge", "category": "Tech News" }
  ]
}
```

Then run:
```bash
python discover_feeds.py websites.json
```

## Sample Output Interpretation

After running the tool, you'll get output like:
```
Starting discovery for 3 sites with 8 workers...
1) Done: https://techcrunch.com -> best: https://techcrunch.com/feed
2) Done: https://arstechnica.com -> best: https://arstechnica.com/rss-feeds/
3) Done: https://www.theverge.com -> best: https://www.theverge.com/rss/index.xml

Wrote 3 entries to feeds_verified.json
Done.
```

The output JSON will contain:
- All tested feed URLs for each site
- HTTP status codes
- Whether each URL is a valid feed
- Number of entries in each feed
- The "best" feed URL (first valid one with entries)

## Tips for Best Results

1. **Start Small**: Test with 5-10 sites first
2. **Check Output**: Review the JSON to see what was found
3. **Adjust Settings**: If you get timeouts, increase `--timeout`
4. **Be Polite**: Don't hammer servers - use appropriate `--delay`
5. **Save Progress**: The tool saves partial results if you Ctrl+C

## Troubleshooting Common Issues

### No feeds found?
Some sites don't have RSS feeds. The tool will still save the results showing what was tested.

### Getting blocked?
Increase the delay: `--delay 1.0`

### Timeouts?
Increase timeout: `--timeout 20`

### Want to resume?
Remove successfully processed sites from your input file and run again.
