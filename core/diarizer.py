import threading
import tempfile
import os
import wave
import numpy as np
import torch
from core.video_utils import extract_audio


class Diarizer:
    def __init__(self):
        self._cancel = False

    def diarize(
        self,
        video_path,
        hf_token="",
        on_progress=None,
        on_complete=None,
        on_error=None,
    ):
        """Run speaker diarization in background thread."""
        self._cancel = False
        thread = threading.Thread(
            target=self._diarize_worker,
            args=(video_path, hf_token, on_progress, on_complete, on_error),
            daemon=True,
        )
        thread.start()
        return thread

    def _diarize_worker(self, video_path, hf_token, on_progress, on_complete, on_error):
        audio_path = None
        try:
            from pyannote.audio import Pipeline

            if on_progress:
                on_progress(0.05)

            # Extract audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                audio_path = temp_audio.name
            extract_audio(video_path, audio_path, format="wav")

            if self._cancel:
                return
            if on_progress:
                on_progress(0.15)

            # Load pipeline (pyannote/huggingface auth argument changed across versions)
            pipeline_kwargs = {}
            if hf_token:
                pipeline_kwargs["token"] = hf_token

            try:
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    **pipeline_kwargs,
                )
            except TypeError as e:
                # Backward compatibility for versions expecting use_auth_token
                if hf_token and "unexpected keyword argument 'token'" in str(e):
                    pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token,
                    )
                else:
                    raise

            if self._cancel:
                return
            if on_progress:
                on_progress(0.3)

            # Run diarization with in-memory waveform to avoid runtime AudioDecoder issues
            diarization_input = self._load_wav_as_waveform_dict(audio_path)
            diarization = pipeline(diarization_input)

            if self._cancel:
                return
            if on_progress:
                on_progress(0.9)

            # Parse results across pyannote output variants
            segments = self._extract_segments(diarization)

            if on_progress:
                on_progress(1.0)
            if on_complete:
                on_complete(segments)

        except Exception as e:
            if on_error:
                on_error(str(e))
        finally:
            if audio_path:
                try:
                    os.remove(audio_path)
                except Exception:
                    pass

    def _extract_segments(self, diarization_output):
        annotation = diarization_output

        # pyannote>=4 returns DiarizeOutput with nested annotation
        if hasattr(diarization_output, "speaker_diarization"):
            annotation = diarization_output.speaker_diarization
        elif isinstance(diarization_output, dict):
            annotation = (
                diarization_output.get("speaker_diarization")
                or diarization_output.get("diarization")
                or diarization_output.get("annotation")
                or diarization_output
            )

        if not hasattr(annotation, "itertracks"):
            raise TypeError(
                f"Unsupported diarization output type: {type(diarization_output).__name__}"
            )

        segments = []
        for turn, _, speaker in annotation.itertracks(yield_label=True):
            segments.append(
                {
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker,
                }
            )
        return segments

    def _load_wav_as_waveform_dict(self, wav_path):
        with wave.open(wav_path, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            n_frames = wav_file.getnframes()
            raw = wav_file.readframes(n_frames)

        if sample_width == 1:
            # PCM unsigned 8-bit
            audio = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
            audio = (audio - 128.0) / 128.0
        elif sample_width == 2:
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sample_width == 4:
            audio = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Unsupported WAV sample width: {sample_width}")

        try:
            audio = audio.reshape(-1, n_channels).T  # (channels, time)
        except ValueError as e:
            raise ValueError("Invalid WAV data shape for diarization input") from e
        waveform = torch.from_numpy(audio).float()
        return {"waveform": waveform, "sample_rate": sample_rate}

    def cancel(self):
        self._cancel = True


def assign_speakers_to_subtitles(subtitles, diarization_segments):
    """For each subtitle, find the speaker with the most temporal overlap."""
    for sub in subtitles:
        best_speaker = ""
        best_overlap = 0.0

        for seg in diarization_segments:
            overlap_start = max(sub.start, seg["start"])
            overlap_end = min(sub.end, seg["end"])
            overlap = max(0.0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = seg["speaker"]

        sub.speaker_id = best_speaker
