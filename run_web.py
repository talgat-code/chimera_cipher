import subprocess
import sys
import os
import webbrowser
import time
import threading


def ensure_flask():
    try:
        import flask
    except ImportError:
        print("Installing Flask...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])


def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    ensure_flask()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    threading.Thread(target=open_browser, daemon=True).start()
    from web.server import app
    print("CHIMERA Cipher Web UI → http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
