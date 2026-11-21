"""Скриншот страницы с эмуляцией мобильного устройства через Chrome DevTools Protocol."""
import base64
import itertools
import json
import subprocess
import sys
import time
import urllib.request

import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9333

width = int(sys.argv[1]) if len(sys.argv) > 1 else 390
height = int(sys.argv[2]) if len(sys.argv) > 2 else 844
url = sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:5000/"
out = sys.argv[4] if len(sys.argv) > 4 else "shot_device.png"
scroll_y = int(sys.argv[5]) if len(sys.argv) > 5 else 0

proc = subprocess.Popen([
    CHROME, "--headless=new", "--disable-gpu",
    f"--remote-debugging-port={PORT}",
    "--user-data-dir=/tmp/chrome-cdp",
    "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    ws_url = None
    for _ in range(50):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json") as r:
                targets = json.load(r)
            page = next(t for t in targets if t["type"] == "page")
            ws_url = page["webSocketDebuggerUrl"]
            break
        except Exception:
            time.sleep(0.3)
    if not ws_url:
        sys.exit("Chrome CDP недоступен")

    ws = websocket.create_connection(ws_url, timeout=30)
    ids = itertools.count(1)

    def cmd(method, **params):
        i = next(ids)
        ws.send(json.dumps({"id": i, "method": method, "params": params}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == i:
                if "error" in msg:
                    sys.exit(f"CDP error: {msg['error']}")
                return msg.get("result", {})

    cmd("Emulation.setDeviceMetricsOverride",
        width=width, height=height, deviceScaleFactor=2, mobile=True)
    cmd("Page.enable")
    cmd("Page.navigate", url=url)
    time.sleep(6)  # загрузка текстур и первые кадры WebGL

    if scroll_y:
        cmd("Runtime.evaluate", expression=f"window.scrollTo(0, {scroll_y})")
        time.sleep(2)

    # Замер переполнения и позиций
    metrics = cmd("Runtime.evaluate", expression="""
      JSON.stringify({
        iw: window.innerWidth,
        bodyW: document.body.scrollWidth,
        docW: document.documentElement.scrollWidth,
      })
    """, returnByValue=True)
    print("metrics:", metrics["result"]["value"])

    shot = cmd("Page.captureScreenshot", format="png")
    with open(out, "wb") as f:
        f.write(base64.b64decode(shot["data"]))
    print("saved", out)
finally:
    proc.terminate()
