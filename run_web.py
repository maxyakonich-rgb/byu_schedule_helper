#!/usr/bin/env python3
"""
Launcher for the BYU Academic Planning Suite & Schedule Solver Web Application.
Starts the local FastAPI server and opens your web browser.
"""
import os
import socket
import sys
import webbrowser

# Ensure working directory and sys.path are set to this project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn
from web_app import app


def find_free_port(starting_port=8000, max_tries=20):
    for port in range(starting_port, starting_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return starting_port


if __name__ == "__main__":
    port = find_free_port(8000)
    url = f"http://localhost:{port}"

    print("\n" + "=" * 65)
    print("🚀 BYU Academic Planning Suite & Schedule Solver Web App")
    print(f"👉 Local Web URL : {url}")
    print("👉 Press Ctrl+C in terminal to stop server")
    print("=" * 65 + "\n")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    uvicorn.run("web_app:app", host="127.0.0.1", port=port, reload=False, log_level="info")
