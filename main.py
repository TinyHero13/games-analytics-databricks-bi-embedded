import os
import sys
import json
import base64
import urllib.request
import urllib.parse
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "instance_url": os.getenv("INSTANCE_URL"),
    "dashboard_id": os.getenv("DASHBOARD_ID"),
    "service_principal_id": os.getenv("SERVICE_PRINCIPAL_ID"),
    "service_principal_secret": os.getenv("SERVICE_PRINCIPAL_SECRET"),
    "external_viewer_id": os.getenv("EXTERNAL_VIEWER_ID"),
    "external_value": os.getenv("EXTERNAL_VALUE"),
    "workspace_id": os.getenv("WORKSPACE_ID"),
    "port": int(os.environ.get("PORT", 3000)),
}

basic_auth = base64.b64encode(
    f"{CONFIG['service_principal_id']}:{CONFIG['service_principal_secret']}".encode()
).decode()

def http_request(url, method="GET", headers=None, body=None):
    headers = headers or {}
    if body is not None and not isinstance(body, (bytes, str)):
        raise ValueError("Body must be bytes or str")

    req = urllib.request.Request(url, method=method, headers=headers)
    if body is not None:
        if isinstance(body, str):
            body = body.encode()
        req.data = body

    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode()
            try:
                return {"data": json.loads(data)}
            except json.JSONDecodeError:
                return {"data": data}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode()}") from None

# -----------------------------------------------------------------------------
# Token logic
# -----------------------------------------------------------------------------
def get_scoped_token():
    oidc_res = http_request(
        f"{CONFIG['instance_url']}/oidc/v1/token",
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        },
        body=urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "scope": "all-apis"
        })
    )
    oidc_token = oidc_res["data"]["access_token"]

    token_info_url = (
        f"{CONFIG['instance_url']}/api/2.0/lakeview/dashboards/"
        f"{CONFIG['dashboard_id']}/published/tokeninfo"
        f"?external_viewer_id={urllib.parse.quote(CONFIG['external_viewer_id'])}"
        f"&external_value={urllib.parse.quote(CONFIG['external_value'])}"
    )
    token_info = http_request(
        token_info_url,
        headers={"Authorization": f"Bearer {oidc_token}"}
    )["data"]

    params = token_info.copy()
    authorization_details = params.pop("authorization_details", None)
    params.update({
        "grant_type": "client_credentials",
        "authorization_details": json.dumps(authorization_details)
    })

    scoped_res = http_request(
        f"{CONFIG['instance_url']}/oidc/v1/token",
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        },
        body=urllib.parse.urlencode(params)
    )
    return scoped_res["data"]["access_token"]

def load_html_template():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Games Analytics - Dashboard BI</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="error-container">
        <h1>Erro: Template não encontrado</h1>
        <p>O arquivo templates/index.html não foi encontrado.</p>
    </div>
</body>
</html>"""

def render_template(template, **kwargs):
    """Simple template renderer that replaces {{variable}} with values"""
    rendered = template
    for key, value in kwargs.items():
        placeholder = f"{{{{{key}}}}}"
        rendered = rendered.replace(placeholder, str(value))
    return rendered

def generate_html(token):
    template = load_html_template()
    return render_template(
        template,
        INSTANCE_URL=CONFIG['instance_url'],
        WORKSPACE_ID=CONFIG['workspace_id'],
        DASHBOARD_ID=CONFIG['dashboard_id'],
        TOKEN=token
    )

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/static/"):
            self.serve_static_file()
            return
            
        # Handle root path with query parameters
        if self.path == "/" or self.path.startswith("/?"):
            try:
                token = get_scoped_token()
                html = generate_html(token)
                status = 200
            except Exception as e:
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Erro - Games Analytics</title>
                    <style>
                        body {{ font-family: system-ui; text-align: center; padding: 50px; background: #f5f5f5; }}
                        .error-container {{ max-width: 500px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                        h1 {{ color: #e53e3e; }}
                        .error-details {{ background: #f7fafc; padding: 1rem; border-radius: 4px; margin: 1rem 0; font-family: monospace; }}
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <h1>Erro no Servidor</h1>
                        <p>Não foi possível carregar o dashboard.</p>
                        <div class="error-details">{str(e)}</div>
                        <button onclick="location.reload()">Tentar Novamente</button>
                    </div>
                </body>
                </html>
                """
                status = 500

            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return
            
        # Handle other paths
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html_404 = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>404 - Page Not Found</title>
            <style>
                body { font-family: system-ui; text-align: center; padding: 50px; background: #f5f5f5; }
                .error-container { max-width: 400px; margin: 0 auto; }
                h1 { color: #e53e3e; }
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>404</h1>
                <p>Página não encontrada</p>
                <a href="/">Voltar ao Dashboard</a>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_404.encode('utf-8'))

    def serve_static_file(self):
        # Remove /static/ prefix and get file path
        file_path = self.path[8:]  # Remove "/static/"
        full_path = os.path.join(os.path.dirname(__file__), "static", file_path)
        
        try:
            # Security check: ensure file is within static directory
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            if not os.path.exists(full_path) or not os.path.commonpath([full_path, static_dir]) == static_dir:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write("Arquivo estático não encontrado".encode('utf-8'))
                return
            
            content_type, _ = mimetypes.guess_type(full_path)
            if content_type is None:
                content_type = "application/octet-stream"
            
            with open(full_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"Erro ao servir arquivo estático: {str(e)}".encode('utf-8'))

def start_server():
    missing = [k for k, v in CONFIG.items() if not v]
    if missing:
        print(f"Missing: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    server = HTTPServer(("0.0.0.0", CONFIG["port"]), RequestHandler)
    print(f"Server running on http://0.0.0.0:{CONFIG['port']}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    start_server()