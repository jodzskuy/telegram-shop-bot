#!/usr/bin/env python3
"""Startup script: run web admin + bot in the same process."""
import os, subprocess, sys

port = os.getenv("PORT", "5000")
root = os.path.dirname(os.path.abspath(__file__))

# Start web admin
web = subprocess.Popen(
    [sys.executable, os.path.join(root, "web", "admin_web.py")],
    env={**os.environ, "PORT": port},
)

# Start bot
bot = subprocess.Popen([sys.executable, os.path.join(root, "bot.py")])

# Wait for both
code = web.wait()
bot.terminate()
sys.exit(code)
