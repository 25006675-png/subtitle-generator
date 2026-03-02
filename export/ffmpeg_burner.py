import subprocess
import threading
import re
import os


QUALITY_PRESETS = {
    "High (slow)": {"crf": "18", "preset": "slow"},
    "Medium (balanced)": {"crf": "23", "preset": "medium"},
    "Low (fast)": {"crf": "28", "preset": "fast"},
}


def check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def burn_subtitles(video_path: str, ass_path: str, output_path: str,
                   quality_preset: str = "Medium (balanced)",
                   on_progress=None, on_complete=None, on_error=None):
    thread = threading.Thread(
        target=_burn_worker,
        args=(video_path, ass_path, output_path, quality_preset,
              on_progress, on_complete, on_error),
        daemon=True,
    )
    thread.start()
    return thread


def _burn_worker(video_path, ass_path, output_path, quality_preset,
                 on_progress, on_complete, on_error):
    try:
        preset = QUALITY_PRESETS.get(quality_preset, QUALITY_PRESETS["Medium (balanced)"])

        # Escape backslashes and colons in ASS path for FFmpeg filter
        ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"ass='{ass_escaped}'",
            "-c:v", "libx264",
            "-crf", preset["crf"],
            "-preset", preset["preset"],
            "-c:a", "copy",
            "-progress", "pipe:1",
            output_path,
        ]

        # Get video duration for progress
        duration = _get_duration(video_path)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        for line in process.stdout:
            line = line.strip()
            if line.startswith("out_time_us="):
                try:
                    us = int(line.split("=")[1])
                    if duration > 0 and on_progress:
                        on_progress(min(us / (duration * 1_000_000), 1.0))
                except ValueError:
                    pass

        process.wait()
        if process.returncode == 0:
            if on_complete:
                on_complete(output_path)
        else:
            stderr = process.stderr.read()
            if on_error:
                on_error(f"FFmpeg error (code {process.returncode}): {stderr[:500]}")

    except Exception as e:
        if on_error:
            on_error(str(e))


def _get_duration(video_path: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0
