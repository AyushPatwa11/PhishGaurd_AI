import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.api import api_bp

# Serve frontend static files from ../frontend
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

app = Flask(
    __name__,
    static_folder=os.path.join(FRONTEND_DIR, "static"),
    static_url_path="/static"
)
CORS(app) # Enable CORS for all routes and origins

# Register API blueprint
app.register_blueprint(api_bp, url_prefix="/api")

# Serve index.html at root
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    target = os.path.join(FRONTEND_DIR, "templates", path)
    if path and os.path.isfile(target):
        return send_from_directory(os.path.join(FRONTEND_DIR, "templates"), path)
    return send_from_directory(os.path.join(FRONTEND_DIR, "templates"), "index.html")

if __name__ == "__main__":
    print("PhishGuard AI running at http://localhost:5000")
    app.run(debug=True, port=5000)
