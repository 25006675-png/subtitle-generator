import threading
from faster_whisper import WhisperModel

class Transcriber:
    def __init__(self):
        self.model = None
        self.model_size = "base"
        self._cancel = False

    def load_model(self, model_size="base"):
        """Load WhisperModel. Sizes: tiny, base, small, medium, large-v2"""
        self.model_size = model_size
        print(f"--- Loading Whisper Model: {model_size} ---")
        try:
             self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
             print(f"--- Model Loaded Successfully ---")
        except Exception as e:
             print(f"--- Error Loading Model: {e} ---")
             raise e

    def transcribe(
        self,
        audio_path,
        language=None,
        voice_adjustment="normal",
        on_progress=None,
        on_complete=None,
        on_error=None,
    ):
        """Run transcription in background thread.
        on_progress(float) - 0.0 to 1.0
        on_complete(list[dict]) - list of {index, start, end, text}
        on_error(str) - error message
        """
        self._cancel = False
        thread = threading.Thread(
            target=self._transcribe_worker,
            args=(audio_path, language, voice_adjustment, on_progress, on_complete, on_error),
            daemon=True,
        )
        thread.start()
        return thread

    def _transcribe_worker(self, audio_path, language, voice_adjustment, on_progress, on_complete, on_error):
        try:
            if self.model is None:
                self.load_model(self.model_size)

            transcribe_kwargs = {
                "language": language,
                "beam_size": 5,
            }

            adjustment = (voice_adjustment or "normal").lower()
            if adjustment == "low":
                transcribe_kwargs["vad_filter"] = True
                transcribe_kwargs["vad_parameters"] = {
                    "min_silence_duration_ms": 900,
                    "speech_pad_ms": 400,
                }
            elif adjustment == "high":
                transcribe_kwargs["vad_filter"] = True
                transcribe_kwargs["vad_parameters"] = {
                    "min_silence_duration_ms": 250,
                    "speech_pad_ms": 200,
                }

            segments, info = self.model.transcribe(audio_path, **transcribe_kwargs)
            duration = info.duration
            results = []
            idx = 0

            for segment in segments:
                if self._cancel:
                    return
                idx += 1
                results.append({
                    "index": idx,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                })
                if on_progress and duration > 0:
                    on_progress(min(segment.end / duration, 1.0))

            if on_progress:
                on_progress(1.0)
            if on_complete:
                on_complete(results)
        except Exception as e:
            if on_error:
                on_error(str(e))

    def cancel(self):
        self._cancel = True

AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large-v2"]
