"""Chat with live Jelena on Render from a Terminal window, exactly as a website visitor would.
Uses the real service (real API cost, real Telegram and email alerts).

Run:  cd ~/Desktop/PROFITLENS-CHATBOT && .venv/bin/python -m tests.live_chat
Type "quit" to stop.
"""
import json
import ssl
import sys
import time
import urllib.error
import urllib.request

import certifi

SERVICE = sys.argv[1] if len(sys.argv) > 1 else "https://profitlens-chat.onrender.com"
CTX = ssl.create_default_context(cafile=certifi.where())


def post(path, body):
    req = urllib.request.Request(SERVICE + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        return json.load(r)


def main():
    sid = "terminal" + time.strftime("%H%M%S")
    print(f"Live chat with Jelena ({SERVICE}). First reply can take up to a minute if the server was asleep.")
    print("Type 'quit' to stop.\n")
    d = post("/start", {"session_id": sid})
    state = d.get("state", "")
    print(f"Jelena: {d['reply']}\n")
    while True:
        try:
            msg = input("You: ").strip()
        except EOFError:
            break
        if msg.lower() in ("quit", "exit"):
            break
        if not msg:
            continue
        print("   (waiting for Jelena...)", flush=True)
        try:
            d = post("/chat", {"session_id": sid, "message": msg, "state": state})
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"   ERROR: {e}. Try again in a moment.\n")
            continue
        state = d.get("state", state)
        print(f"Jelena: {d['reply']}")
        if d.get("mode") not in ("chat", None):
            print(f"   (the website would now show: {d['mode']})")
        print()
    print(f"Chat ended. In Telegram this chat is labelled with {sid[-6:]}.")


if __name__ == "__main__":
    main()
