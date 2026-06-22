# krack

Download course media (videos & PDFs) from [krack.ai](https://krack.ai).

## Usage

```bash
pip install requests beautifulsoup4 urllib3
```

Place your krack.ai session cookies in `cookies.txt` as a JSON object or array of `{name, value}` pairs.

```bash
python krack.py [COURSE_URL] [--out DOWNLOAD_DIR] [--cookies COOKIES_PATH]
```

Defaults:
- **COURSE_URL**: `https://krack.ai/courses/learn-ukulele/`
- **OUT dir**: `downloads`
- **Cookies**: `cookies.txt`

Files are organized into folders named after course sections.
