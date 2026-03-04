import time
import threading
from core.diarizer import Diarizer
from core.config import HF_TOKEN

VIDEO_PATH = r"C:\Users\choon\Downloads\THE Millennial Job Interview (1).mp4"

done = threading.Event()
result = {"status": None, "segments": 0, "error": ""}


def on_progress(p):
    print(f"PROGRESS {int(p * 100)}%", flush=True)


def on_complete(segments):
    result["status"] = "ok"
    result["segments"] = len(segments)
    print(f"COMPLETE segments={len(segments)}", flush=True)
    done.set()


def on_error(msg):
    result["status"] = "error"
    result["error"] = msg
    print(f"ERROR {msg}", flush=True)
    done.set()


if __name__ == "__main__":
    print("START diarization test", flush=True)
    diarizer = Diarizer()
    diarizer.diarize(
        VIDEO_PATH,
        hf_token=HF_TOKEN,
        on_progress=on_progress,
        on_complete=on_complete,
        on_error=on_error,
    )

    start = time.time()
    while not done.wait(5):
        elapsed = int(time.time() - start)
        print(f"HEARTBEAT elapsed={elapsed}s", flush=True)

    if result["status"] == "ok":
        print("TEST_PASS", flush=True)
    else:
        print("TEST_FAIL", flush=True)
        raise SystemExit(1)
