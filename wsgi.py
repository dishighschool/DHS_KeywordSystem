"""WSGI entrypoint for production servers."""
from __future__ import annotations

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # For direct execution (e.g., Pterodactyl without gunicorn)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
