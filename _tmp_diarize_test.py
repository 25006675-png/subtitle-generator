import time
from core.diarizer import Diarizer
from core.config import HF_TOKEN

video = r"C:\Users\choon\Downloads\THE Millennial Job Interview (1).mp4"
d = Diarizer()
state = {"done": False, "ok": False, "count": 0, "error": ""}


def on_progress(_p):
    pass


def on_complete(segments):
    state["done"] = True
    state["ok"] = True
    state["count"] = len(segments)


def on_error(msg):
    state["done"] = True
    state["error"] = msg


d.diarize(video, hf_token=HF_TOKEN, on_progress=on_progress, on_complete=on_complete, on_error=on_error)
for _ in range(900):
    if state["done"]:
        break
    time.sleep(0.5)

print(state)
raise SystemExit(0 if state["ok"] else 1)
