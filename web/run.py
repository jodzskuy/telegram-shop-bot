#!/usr/bin/env python3
"""Runner for web app - bypasses gunicorn issues on Railway."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web import app as web_app

port = int(os.getenv("PORT", 5000))
web_app.app.run(host="0.0.0.0", port=port)
