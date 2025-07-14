import os
import time
import asyncio
import uuid
from quart import Quart, request as quart_request, jsonify, send_file, Response, render_template_string
from functools import wraps
from botasaurus_requests import request as br_request
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

# -------- Settings --------
API_KEYS = {"test-key-123", "another-key-456"}  # Set valid API keys here or load from env/DB
RATE_LIMIT = 60  # max requests per key per minute

# -------- Globals --------
app = Quart(__name__)
executor = ThreadPoolExecutor(max_workers=10)
rate_limit_data = defaultdict(lambda: deque())

# -------- Templates --------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Botasaurus Requests API Service</title>
  <style>body{font-family:sans-serif;max-width:600px;margin:40px auto;color:#333;}code{background:#eee;padding:2px 6px;}</style>
</head>
<body>
  <h1>🦖 Botasaurus Requests API Service</h1>
  <p>This API lets you proxy HTTP requests using stealth anti-bot techniques.<br>
     <b>Auth required:</b> Pass your <code>X-API-Key</code> as a header.</p>
  <h2>Endpoints</h2>
  <h3>POST /api/request</h3>
  <pre>{
  "url": "https://httpbin.org/headers",
  "method": "GET",         // GET, POST, PUT, DELETE
  "headers": {...},        // Optional request headers
  "data": "...",           // POST/PUT body (optional)
  "files": {...},          // For upload (multipart), see below
  "only": "body"           // "body", "headers", "status", "curl"
}</pre>
  <h3>Returns</h3>
  <ul>
    <li><code>body</code> — Only the response body as text</li>
    <li><code>headers</code> — Only the response headers (JSON)</li>
    <li><code>status</code> — Only the HTTP status code</li>
    <li><code>curl</code> — curl command for the request</li>
    <li>(Omit <code>only</code> for full response JSON)</li>
  </ul>
  <h3>Example (Python)</h3>
  <pre>
import requests
r = requests.post("http://localhost:5000/api/request",
    headers={"X-API-Key": "test-key-123"},
    json={"url": "https://httpbin.org/get", "method": "GET", "only": "body"})
print(r.text)
  </pre>
  <h3>File Upload</h3>
  <pre>
curl -X POST http://localhost:5000/api/request \\
    -H "X-API-Key: test-key-123" \\
    -F url="https://httpbin.org/post" \\
    -F method="POST" \\
    -F only="body" \\
    -F file=@/path/to/file
  </pre>
  <hr>
  <p>Made with 🦖 <b>Botasaurus Requests</b> | See <a href="https://github.com/omkarcloud/botasaurus-requests">Docs</a></p>
</body>
</html>
"""

# -------- Helpers --------
def require_apikey(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        key = quart_request.headers.get("X-API-Key")
        if not key or key not in API_KEYS:
            return jsonify({"error": "Unauthorized: Missing or invalid API key"}), 401
        # rate limiting
        q = rate_limit_data[key]
        now = time.time()
        # Remove old timestamps
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            return jsonify({"error": "Rate limit exceeded"}), 429
        q.append(now)
        return await func(*args, **kwargs)
    return wrapper

def make_curl_command(method, url, headers, data, files=None):
    cmd = ["curl", "-X", method]
    for k, v in (headers or {}).items():
        cmd.extend(["-H", f"{k}: {v}"])
    if data:
        cmd.extend(["--data", data])
    if files:
        for field, fileinfo in files.items():
            cmd.extend(["-F", f"{field}=@{fileinfo['filename']}"])
    cmd.append(url)
    return " ".join(cmd)

async def run_in_executor(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))

# -------- Routes --------

@app.route("/")
async def index():
    return Response(INDEX_HTML, content_type="text/html")

@app.route("/api/request", methods=["POST"])
@require_apikey
async def api_request():
    # Support both JSON and multipart (for file upload)
    if quart_request.content_type and "multipart/form-data" in quart_request.content_type:
        form = await quart_request.form
        url = form.get("url")
        method = (form.get("method") or "GET").upper()
        data = form.get("data")
        only = form.get("only")
        headers = {}
        # handle file
        files = {}
        if "file" in quart_request.files:
            fileobj = await quart_request.files.get("file")
            temp_name = f"/tmp/{uuid.uuid4().hex}_{fileobj.filename}"
            await fileobj.save(temp_name)
            files = {"file": open(temp_name, "rb")}
        else:
            files = None
    else:
        payload = await quart_request.get_json(force=True)
        url = payload.get("url")
        method = (payload.get("method") or "GET").upper()
        headers = payload.get("headers") or {}
        data = payload.get("data")
        only = payload.get("only")
        files = None

    # Validation
    if not url or method not in {"GET","POST","PUT","DELETE"}:
        return jsonify({"error": "Invalid url or method"}), 400

    # Use botasaurus_requests in thread (to avoid blocking)
    req_func = getattr(br_request, method.lower(), None)
    try:
        resp = await run_in_executor(
            req_func, url, headers=headers, data=data, files=files
        )
    except Exception as e:
        return jsonify({"error": f"Request failed: {str(e)}"}), 500

    # Clean up temp files if any
    if files and "file" in files:
        files["file"].close()
        try: os.remove(files["file"].name)
        except Exception: pass

    # Format response
    if only == "body":
        return Response(resp.text, content_type="text/plain")
    elif only == "headers":
        return jsonify(dict(resp.headers))
    elif only == "status":
        return jsonify({"status_code": resp.status_code})
    elif only == "curl":
        curl_cmd = make_curl_command(method, url, headers, data, files)
        return jsonify({"curl": curl_cmd})
    else:
        return jsonify({
            "url": resp.url,
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text
        })

# -------- Run --------
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=5000)
