import os
import signal
import sys
import threading
import time
import webview
from flask import Flask
from lib.db import *

app = Flask(__name__)


@app.route("/")
def index():
    return "Welcome to Bookkeeppr!"


def run_flask():
    app.run(port=1304)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Give Flask a moment to start
    time.sleep(1)

    # Launch embedded browser window
    window = webview.create_window(
        "Bookkeeppr", "http://localhost:1304", width=1000, height=700
    )

    try:
        webview.start()
    finally:
        # When the window closes, terminate the app
        print("[APP] Window closed, exiting...")
        sys.exit(0)
