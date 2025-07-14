# BotaRequests + Quart as a Service
Botasaurus Requests is a stealth HTTP client for Python web scraping and crawling. It bypasses anti-bot systems (Cloudflare, Akamai, etc) without using a browser, by emulating real browser TLS and HTTP signatures. It is lightweight, cross-platform, and offers drop-in compatibility with `requests`.

Forked from [hrequests], Botasaurus Requests is streamlined, faster, and Windows/Mac/Linux friendly. It powers the Botasaurus anti-detect scraping ecosystem.

---

## 🚀 Features

* **Stealth HTTP Requests:** Sends browser-like HTTP headers in real order, uses real TLS fingerprints, and mimics Chrome or Firefox network stack.
* **Cloudflare/Akamai Bypass:** Fetches anti-bot protected pages (tested with Cloudflare, Akamai) over pure HTTP.
* **HTTP/2 + Brotli/Gzip:** True HTTP/2 and modern content encoding support.
* **Super Fast HTML Parsing:** Integrated parser (selectolax) \~25x faster than BeautifulSoup.
* **Parallel & Async Support:** Dispatch many requests in parallel with simple Python lists.
* **Persistent Sessions:** Manage login/cookies like a browser.
* **Browser/OS Fingerprint:** Choose or randomize browser, version, and OS.
* **Proxy Support:** HTTP/S proxies with one parameter.
* **Familiar API:** Looks and feels like Python `requests`.
* **No Browser Needed:** No Selenium, Playwright, Chromedriver.
* **Cross-Platform:** Works on Windows, Mac, Linux.
* **Google Referer by Default:** GET requests auto-include a Google search referer.
* **Robust & Lightweight:** No Playwright dependency, small install, quick start.

---

## 📦 Installation

```bash
pip install botasaurus-requests
```

---

## ✨ Quick Start

```python
from botasaurus_requests import request

response = request.get("https://httpbin.org/headers")
print(response.status_code)
print(response.text)
```

**Sample Output (headers returned by httpbin):**

```json
{
  "headers": {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Host": "httpbin.org",
    "Referer": "https://www.google.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
  }
}
```

---

## 🧑‍💻 Tutorial: Stealth Scraping in Action

### 1. Stealth GET

```python
from botasaurus_requests import request

url = "https://www.g2.com/products/omkar-cloud/reviews"
resp = request.get(url)
print(resp.status_code)   # Should print 200 (if bypass succeeds)
print(resp.text[:500])    # Print first 500 chars of page HTML
```

---

### 2. Parse HTML with Your Favorite Parser

```python
from bs4 import BeautifulSoup

resp = request.get("https://example.org/")
soup = BeautifulSoup(resp.text, "html.parser")
print(soup.find("h1").get_text())
```

Or with built-in ultra-fast parser:

```python
print(resp.html.find("h1")[0].text())
```

---

### 3. Use Sessions for Login

```python
from botasaurus_requests import Session

session = Session()
resp = session.post("https://example.com/login", data={"username":"user", "password":"pass"})
dashboard = session.get("https://example.com/user/dashboard")
print(dashboard.text)
```

---

### 4. Choose Browser/OS Fingerprint

```python
from botasaurus_requests import chrome, firefox

chrome_sess = chrome.Session()  # Random Chrome profile
firefox_sess = firefox.Session(os="mac")
```

---

### 5. Use Proxies

```python
response = request.get(
    "https://httpbin.org/ip",
    proxy="http://username:password@proxyhost:port"
)
print(response.text)
```

---

### 6. Parallel & Async Requests

#### Fire Many Requests at Once

```python
urls = ["https://httpbin.org/delay/1", "https://httpbin.org/delay/2"]
responses = request.get(urls)
for r in responses:
    print(r.url, r.status_code)
```

#### Advanced Async

```python
from botasaurus_requests import map, request

reqs = [
    request.async_get("https://httpbin.org/status/200"),
    request.async_get("https://httpbin.org/status/404"),
]
resps = map(reqs)
for resp in resps:
    print(resp.url, resp.status_code)
```

Limit concurrency:

```python
results = map(reqs, size=10)
```

Streaming responses as they arrive (unordered):

```python
from botasaurus_requests import imap
for resp in imap(reqs, size=2):
    print(resp.status_code, resp.url)
```

---

### 7. Fire-and-Forget (nohup)

```python
lazy_resp = request.get("https://httpbin.org/delay/5", nohup=True)
# do other stuff ...
print(lazy_resp.text)  # blocks until response is ready
```

---

## 🧩 API Overview

* `request.get(url, **kwargs)`
* `request.post(url, **kwargs)`
* `request.async_get(url, **kwargs)` — create async requests
* `map([requests], size=n)` — batch send concurrently
* `imap([requests], size=n)` — unordered async results
* `Session(...)` — persistent cookies/headers
* `chrome.Session()` / `firefox.Session()`
* `.proxy`, `.user_agent`, `.os` supported everywhere

**Response object:**

* `.status_code` — HTTP status
* `.headers` — response headers
* `.text` — decoded body
* `.content` — raw bytes
* `.cookies` — cookies set by server
* `.json()` — parse JSON
* `.raise_for_status()` — raise for 4xx/5xx
* `.elapsed`, `.history`, `.ok`
* `.html.find(selector)` — built-in fast selectolax parser

---

## How to run the server.py

hypercorn main:app --bind 0.0.0.0:5000 --workers 4
# or
gunicorn main:app -k quart.worker --bind 0.0.0.0:5000 --workers 4


## 🏆 Best Practices & Tips

* **Rotate Profiles:** For repeated scraping, stick to one browser fingerprint per session; for single-shot, randomize.
* **Respect robots.txt and site rate limits.** Use `map(..., size=n)` for polite scraping.
* **Use proxies** for large-scale or sensitive scraping.
* **Handle errors:** Use try/except, or `exception_handler` with `map/imap`.
* **If all else fails:** Use a real browser only as a last resort.

---

## ⚠️ Disclaimer

Botasaurus Requests is for **educational, ethical, and legal use only**.
Always comply with website terms and local laws.

---

## ⭐ Credits

Forked from [hrequests](https://github.com/daijro/hrequests) by [daijro](https://github.com/daijro).
Enhanced by Omkar Cloud.
Licensed under Apache-2.0.

---

## 🔗 See Also

* [Botasaurus Framework](https://github.com/omkarcloud/botasaurus) – Full browser automation + anti-bot scraping suite.

---

**Happy Scraping!**
