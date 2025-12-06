# RSS/Atom Feed Discovery Tool

A tool that automatically discovers RSS and Atom feeds from websites. Simply provide a list of website URLs, and this tool will intelligently search for and verify their feed URLs.

## 🌟 Features

- **Smart Feed Discovery**: Automatically discovers RSS/Atom feeds by:
  - Parsing HTML `<link>` tags for feed references
  - Checking common feed URL patterns (`/feed`, `/rss`, `/atom.xml`, etc.)
  - Following redirects to find the actual feed location
  - Verifying feed validity using feedparser

- **Multiple Input Formats**: Supports both CSV and JSON input files
- **Concurrent Processing**: Uses multi-threading for fast parallel processing of multiple websites
- **Graceful Interruption**: Ctrl+C saves partial results instead of losing all progress
- **Detailed Output**: Generates comprehensive JSON reports with all discovered feeds and metadata
- **Polite Crawling**: Built-in rate limiting to respect server resources

## 📋 Requirements

- Python 3.7+
- Required packages:
  ```
  requests
  beautifulsoup4
  feedparser
  colorama (optional, for colored output)
  ```

## 🚀 Installation

1. Clone this repository and navigate to it:
   ```bash
   git clone https://github.com/yourusername/url-to-feed.git
   cd url-to-feed  # ⚠️ Important: Navigate into the directory!
   ```

2. Install dependencies:
   
   **Linux/Mac (bash):**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   pip install -r requirements.txt
   ```
   
   **Windows (PowerShell):**
   ```powershell
   pip install -r requirements.txt
   ```

3. Create your input file from the example:
   
   **Linux/Mac (bash):**
   ```bash
   # For JSON input (with metadata)
   cp websites.example.json websites.json
   # OR for simple JSON (URLs only)
   cp websites.simple.example.json websites.json
   # OR for CSV input (with metadata)
   cp websites.example.csv websites.csv
   # OR for simple CSV (URLs only)
   cp websites.simple.example.csv websites.csv
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   REM For JSON input (with metadata)
   copy websites.example.json websites.json
   REM OR for simple JSON (URLs only)
   copy websites.simple.example.json websites.json
   REM OR for CSV input (with metadata)
   copy websites.example.csv websites.csv
   REM OR for simple CSV (URLs only)
   copy websites.simple.example.csv websites.csv
   ```
   
   **Windows (PowerShell):**
   ```powershell
   # For JSON input (with metadata)
   Copy-Item websites.example.json websites.json
   # OR for simple JSON (URLs only)
   Copy-Item websites.simple.example.json websites.json
   # OR for CSV input (with metadata)
   Copy-Item websites.example.csv websites.csv
   # OR for simple CSV (URLs only)
   Copy-Item websites.simple.example.csv websites.csv
   ```
   
   Then edit `websites.json` or `websites.csv` with your own website URLs.

## 📖 Usage

### Basic Usage

**Linux/Mac/Windows (all terminals):**
```bash
python discover_feeds.py websites.json
```

or with explicit flags:

```bash
python discover_feeds.py -i websites.json -o output.json
```

> **Note**: 
> - The `python` command works across bash, Command Prompt, and PowerShell.
> - On Windows, you can also use `py` instead of `python` (e.g., `py discover_feeds.py websites.json`).

### 📂 Important: File Paths

**Option 1: Run from the same directory (Recommended)**
```bash
# Navigate to the project directory first
cd path/to/url-to-feed

# Then run the script (files are in the same folder)
python discover_feeds.py websites.json
```

**Option 2: Specify full/relative paths**
```bash
# If your input file is elsewhere, provide the full path
python discover_feeds.py C:\Users\YourName\Documents\my-websites.json

# Or relative path
python discover_feeds.py ../data/websites.json -o ../output/feeds.json
```

> **💡 Tip**: For simplicity, keep your input file (`websites.json`) in the same folder as `discover_feeds.py`.

### Command Line Arguments

```
positional arguments:
  input_path            Input file (CSV or JSON)

optional arguments:
  -h, --help            Show help message and exit
  -i, --input INPUT     Input CSV or JSON file
  -o, --output OUTPUT   Output JSON file (default: feeds_verified.json)
  -w, --workers WORKERS Number of worker threads (default: 8)
  --timeout TIMEOUT     Request timeout in seconds (default: 10)
  --delay DELAY         Politeness delay between requests in seconds (default: 0.12)
```

### Examples

**Process a JSON file with custom output:**
```bash
python discover_feeds.py websites.json -o my_feeds.json
# Windows alternative: py discover_feeds.py websites.json -o my_feeds.json
```

**Process a CSV file with more workers:**
```bash
python discover_feeds.py sites.csv -w 16
# Windows alternative: py discover_feeds.py sites.csv -w 16
```

**Adjust timeout and delay:**
```bash
python discover_feeds.py websites.json --timeout 15 --delay 0.2
# Windows alternative: py discover_feeds.py websites.json --timeout 15 --delay 0.2
```

## 📁 Input File Formats

> **Note**: Example template files are provided:
> - **With metadata**: `websites.example.json` and `websites.example.csv` (includes name and category fields)
> - **Simple (URLs only)**: `websites.simple.example.json` and `websites.simple.example.csv` (just URLs)
> 
> Copy whichever format suits your needs!

### JSON Format

The tool supports multiple JSON structures:

**Option 1: Array of objects with URL field** (see `websites.example.json`)
```json
{
  "websites": [
    { "url": "https://example.com", "name": "Example Site", "category": "Tech" },
    { "url": "https://blog.example.org", "name": "Example Blog" }
  ]
}
```

**Option 2: Simple array of strings** (see `websites.simple.example.json`) ⭐ **Simplest format**
```json
[
  "https://example.com",
  "https://blog.example.org"
]
```

**Option 3: Simple object with string values**
```json
{
  "site1": "https://example.com",
  "site2": "https://blog.example.org"
}
```

### CSV Format

**With header** (see `websites.example.csv`)
```csv
url,name,category
https://example.com,Example Site,Tech
https://blog.example.org,Example Blog,Writing
```

**Without header - URLs only** (see `websites.simple.example.csv`) ⭐ **Simplest format**
```csv
https://example.com
https://blog.example.org
```

The tool automatically detects headers and looks for columns named `domain`, `url`, `site`, or `website`.

## 📤 Output Format

The tool generates a JSON file with detailed results:

```json
{
  "results": [
    {
      "name": "https://example.com",
      "site": "https://example.com",
      "candidates": [
        {
          "url": "https://example.com/feed",
          "final_url": "https://example.com/feed",
          "http_status": 200,
          "content_type": "application/xml",
          "is_feed": true,
          "entries": 10,
          "error": null
        }
      ],
      "best": "https://example.com/feed"
    }
  ]
}
```

### Output Fields

- **name**: Original input domain/URL
- **site**: Normalized site URL
- **candidates**: Array of all tested feed URLs with details:
  - `url`: Tested URL
  - `final_url`: Final URL after redirects
  - `http_status`: HTTP response code
  - `content_type`: Content-Type header
  - `is_feed`: Whether it's a valid feed
  - `entries`: Number of feed entries found
  - `error`: Error message if any
- **best**: The best feed URL found (first valid feed with entries)

## 🔍 How It Works

1. **Normalization**: Converts domain inputs to proper URLs
2. **Homepage Parsing**: Fetches the homepage and looks for:
   - `<link>` tags with RSS/Atom types
   - Anchor tags containing feed-related keywords
3. **Common Paths**: Tests common feed URL patterns
4. **Validation**: Verifies each candidate URL by:
   - Checking HTTP status
   - Examining Content-Type headers
   - Parsing content with feedparser
   - Counting feed entries
5. **Best Selection**: Chooses the first valid feed with entries

## ⚙️ Configuration

You can modify these constants in the script:

```python
REQUEST_TIMEOUT = 10              # Request timeout in seconds
SLEEP_BETWEEN_REQUESTS = 0.12     # Delay between requests
MAX_WORKERS = 8                   # Number of concurrent threads
```

Common feed paths checked:
```python
COMMON_FEED_PATHS = [
    "/feed", "/feed/", "/rss", "/rss.xml", "/atom.xml",
    "/index.xml", "/index.rdf", "/feeds/posts/default",
    "/?format=rss", "/?format=xml", "/?feed=rss",
    "/blog/feed", "/blog/rss", "/rss.php",
]
```

## 🛑 Graceful Interruption

Press `Ctrl+C` to stop the process. The tool will:
- Stop submitting new work
- Wait briefly for running tasks to complete
- Save all completed results to the output file
- Display a summary of partial results

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 🐛 Troubleshooting

**Issue**: No feeds found for a website
- **Solution**: Some sites may not have RSS feeds. Check the website manually or try alternative feed discovery services.

**Issue**: Timeout errors
- **Solution**: Increase the timeout value: `--timeout 20`

**Issue**: Rate limiting or blocking
- **Solution**: Increase the delay between requests: `--delay 0.5`

**Issue**: Too slow
- **Solution**: Increase worker threads (but be respectful): `--workers 16`

## 💡 Tips

- Start with a small batch to test before processing large lists
- Use appropriate worker counts based on your internet connection
- Respect website rate limits by adjusting the delay parameter
- Some websites may block automated requests - consider adding custom User-Agent headers
- The tool saves partial results on interruption, so you can resume later by removing processed sites from input

## 📊 Example Workflow

1. Create a JSON file with your websites:
   ```json
   {
     "websites": [
       { "url": "https://blog.example.com" },
       { "url": "https://news.example.org" }
     ]
   }
   ```

2. Run the discovery tool:
   ```bash
   python discover_feeds.py websites.json -o feeds.json
   # Windows alternative: py discover_feeds.py websites.json -o feeds.json
   ```

3. Check the output:
   
   **Linux/Mac (bash):**
   ```bash
   cat feeds.json
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   type feeds.json
   ```
   
   **Windows (PowerShell):**
   ```powershell
   Get-Content feeds.json
   ```

4. Use the discovered feeds in your RSS reader or application!

## 🔗 Use Cases

- Building RSS feed aggregators
- Creating reading lists for RSS readers
- Monitoring multiple blogs and news sites
- Research and content curation
- Automated content discovery pipelines
