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
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Botasaurus Requests API Service</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background: #fafbfc; }
    .container { max-width: 850px; margin-top: 40px; }
    pre, code { background: #f3f3f3 !important; }
    .tab-content { margin-top: 18px; }
    .badge-custom { background: #22223b; color: #fff; }
  </style>
</head>
<body>
<div class="container shadow p-4 bg-white rounded-4">
  <h1 class="mb-3">🦖 Botasaurus Requests <span class="badge badge-custom">API Service</span></h1>
  <p class="lead">
    Proxy HTTP requests through powerful anti-bot bypasses.  
    <br>
    <b>Auth required:</b> Pass your <code>X-API-Key</code> in the request header.
  </p>
  <ul class="nav nav-tabs" id="docTabs" role="tablist">
    <li class="nav-item" role="presentation">
      <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview"
              type="button" role="tab" aria-controls="overview" aria-selected="true">Overview</button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="endpoints-tab" data-bs-toggle="tab" data-bs-target="#endpoints"
              type="button" role="tab" aria-controls="endpoints" aria-selected="false">Endpoints</button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="examples-tab" data-bs-toggle="tab" data-bs-target="#examples"
              type="button" role="tab" aria-controls="examples" aria-selected="false">Examples</button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="upload-tab" data-bs-toggle="tab" data-bs-target="#upload"
              type="button" role="tab" aria-controls="upload" aria-selected="false">File Upload</button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="response-tab" data-bs-toggle="tab" data-bs-target="#response"
              type="button" role="tab" aria-controls="response" aria-selected="false">Response Types</button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="faq-tab" data-bs-toggle="tab" data-bs-target="#faq"
              type="button" role="tab" aria-controls="faq" aria-selected="false">FAQ / Tips</button>
    </li>
  </ul>
  <div class="tab-content" id="docTabsContent">

    <!-- Overview Tab -->
    <div class="tab-pane fade show active" id="overview" role="tabpanel" aria-labelledby="overview-tab">
      <p>
        <b>Botasaurus Requests API Service</b> is a powerful HTTP proxy microservice for web automation, scraping, and robust data gathering.<br>
        It automatically mimics browser traffic and bypasses advanced anti-bot protections (Cloudflare, Akamai, etc).
      </p>
      <ul>
        <li>Works with <b>GET, POST, PUT, DELETE</b> methods</li>
        <li>Supports custom headers, data, and file uploads</li>
        <li>Returns only what you need: body, headers, status, or curl command</li>
        <li>Limits & protects with API Key and rate limiting (per minute)</li>
        <li>Ideal for scraping, testing, or stealth proxying</li>
      </ul>
    </div>

    <!-- Endpoints Tab -->
    <div class="tab-pane fade" id="endpoints" role="tabpanel" aria-labelledby="endpoints-tab">
      <h5>POST <code>/api/request</code></h5>
      <p>
        <b>Headers:</b> <code>X-API-Key: &lt;your-api-key&gt;</code>
      </p>
      <b>JSON Payload (for GET/POST/PUT/DELETE):</b>
      <pre>{
  "url": "https://httpbin.org/headers",
  "method": "GET",          // GET, POST, PUT, DELETE (default: GET)
  "headers": { ... },       // Optional dict of HTTP headers
  "data": "...",            // Optional body (string or form, for POST/PUT)
  "only": "body"            // "body", "headers", "status", "curl" (default: all)
}</pre>
      <b>Multipart Form (for file upload):</b>
      <pre>
url=https://httpbin.org/post
method=POST
only=body
file=@/path/to/file
      </pre>
      <p>
        Omit <code>only</code> to get the full JSON (status, headers, body).
      </p>
      <p class="text-info">
        <b>Note:</b> Rate limited per API key for fair use.
      </p>
    </div>

    <!-- Examples Tab -->
    <div class="tab-pane fade" id="examples" role="tabpanel" aria-labelledby="examples-tab">
      <h5>Python Example (requests):</h5>
      <pre>
import requests
r = requests.post("http://localhost:5000/api/request",
    headers={"X-API-Key": "test-key-123"},
    json={
      "url": "https://httpbin.org/get",
      "method": "GET",
      "only": "headers"
    })
print(r.json())
      </pre>
      <h5>cURL Example:</h5>
      <pre>
curl -X POST http://localhost:5000/api/request \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://httpbin.org/get","method":"GET","only":"body"}'
      </pre>
      <h5>Get Only Status Code:</h5>
      <pre>
{
  "url": "https://httpbin.org/status/418",
  "method": "GET",
  "only": "status"
}
      </pre>
    </div>

    <!-- File Upload Tab -->
    <div class="tab-pane fade" id="upload" role="tabpanel" aria-labelledby="upload-tab">
      <h5>Upload a File via POST:</h5>
      <pre>
curl -X POST http://localhost:5000/api/request \
  -H "X-API-Key: test-key-123" \
  -F url="https://httpbin.org/post" \
  -F method="POST" \
  -F only="body" \
  -F file=@/path/to/file
      </pre>
      <p>
        The API will upload your file to the target URL using a real browser fingerprint.<br>
        Multiple files and form fields can also be handled; see your HTTP client documentation.
      </p>
      <p>
        <b>Returns:</b> The body of the response (e.g. JSON with file info if using httpbin).
      </p>
    </div>

    <!-- Response Types Tab -->
    <div class="tab-pane fade" id="response" role="tabpanel" aria-labelledby="response-tab">
      <h5>Return Values</h5>
      <ul>
        <li><b>body</b>: returns only the raw body as text.</li>
        <li><b>headers</b>: returns all response headers as JSON.</li>
        <li><b>status</b>: returns <code>{"status_code": 200}</code> or other HTTP code.</li>
        <li><b>curl</b>: returns a ready-to-use <code>curl</code> command string.</li>
        <li><b>default</b>: full response object (status, headers, body).</li>
      </ul>
      <p>All error conditions return a JSON with <code>error</code> key and appropriate HTTP status.</p>
      <b>Example of full JSON response:</b>
      <pre>
{
  "url": "https://httpbin.org/get",
  "status_code": 200,
  "headers": {
    "Content-Type": "application/json",
    ...
  },
  "body": "{...}"
}
      </pre>
    </div>

    <!-- FAQ Tab -->
    <div class="tab-pane fade" id="faq" role="tabpanel" aria-labelledby="faq-tab">
      <h5>Frequently Asked Questions & Tips</h5>
      <ul>
        <li><b>Is it really stealth?</b> Yes! Every request uses browser-grade TLS + headers.</li>
        <li><b>What does API key do?</b> Protects the service and applies rate limits.</li>
        <li><b>Can I use custom headers?</b> Yes, supply any headers you want in the <code>headers</code> dict.</li>
        <li><b>Why use this?</b> For anti-bot bypass, scraping, automated QA, or as a safe HTTP relay.</li>
        <li><b>What if I get a 429?</b> You’ve hit your rate limit. Wait or upgrade your plan.</li>
        <li><b>Can I scrape websites with Cloudflare?</b> In most cases, yes, even when <code>requests</code> or <code>curl</code> fails directly!</li>
        <li><b>What’s returned on error?</b> Always JSON like <code>{"error": "description"}</code></li>
      </ul>
    </div>

  </div>
  <hr>
  <p class="mt-3">
    Made with 🦖 <b>Botasaurus Requests</b> | 
    <a href="https://github.com/omkarcloud/botasaurus-requests" target="_blank">GitHub & Docs</a>
  </p>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
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
def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    ssl_ctx = ("cert.crt", "cert.key")  # Paths to your cert and key
    app.run(host="0.0.0.0", port=5000, ssl_context=ssl_ctx)

if __name__ == "__main__":
    main()
