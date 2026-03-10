import threading
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
BATCH_SIZE = 50

LANGUAGES = [
    "Afrikaans", "Arabic", "Armenian", "Azerbaijani", "Belarusian", "Bosnian",
    "Bulgarian", "Catalan", "Chinese (Simplified)", "Chinese (Traditional)",
    "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Filipino",
    "Finnish", "French", "Galician", "Georgian", "German", "Greek", "Hebrew",
    "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese",
    "Kannada", "Kazakh", "Korean", "Latvian", "Lithuanian", "Macedonian",
    "Malay", "Marathi", "Mongolian", "Norwegian", "Persian", "Polish",
    "Portuguese", "Romanian", "Russian", "Serbian", "Slovak", "Slovenian",
    "Spanish", "Swahili", "Swedish", "Tamil", "Telugu", "Thai", "Turkish",
    "Ukrainian", "Urdu", "Vietnamese", "Welsh"
]

class Translator:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self._cancel = False

    def translate(self, entries, target_language, on_progress=None, on_complete=None, on_error=None):
        """Translate subtitle entries in batches using background thread.
        entries: list of SubtitleEntry objects
        target_language: target language name
        on_progress(float) - 0.0 to 1.0
        on_complete(dict) - {index: translated_text}
        on_error(str) - error message
        """
        self._cancel = False
        thread = threading.Thread(target=self._translate_worker,
                                  args=(entries, target_language, on_progress, on_complete, on_error),
                                  daemon=True)
        thread.start()
        return thread

    def _translate_worker(self, entries, target_language, on_progress, on_complete, on_error):
        try:
            translations = {}
            total = len(entries)

            for batch_start in range(0, total, BATCH_SIZE):
                if self._cancel:
                    return

                batch = entries[batch_start:batch_start + BATCH_SIZE]
                numbered_lines = "\n".join(f"{e.index}|{e.original_text}" for e in batch)

                prompt = (
                    f"Translate the following numbered subtitle lines to {target_language}. "
                    f"For technical terms and proper nouns, translate only if a widely accepted translation exists; otherwise keep the original. "
                    f"Return ONLY the translations in the exact same numbered format: number|translated text. "
                    f"Keep the numbering identical. Do not add explanations.\n\n"
                    f"{numbered_lines}"
                )

                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                response_text = (response.text or "").strip()

                for line in response_text.split("\n"):
                    line = line.strip()
                    if "|" in line:
                        parts = line.split("|", 1)
                        try:
                            idx = int(parts[0].strip())
                            text = parts[1].strip()
                            translations[idx] = text
                        except (ValueError, IndexError):
                            continue

                if on_progress:
                    done = min(batch_start + BATCH_SIZE, total)
                    on_progress(done / total)

            if on_complete:
                on_complete(translations)
        except Exception as e:
            if on_error:
                on_error(str(e))

    def cancel(self):
        self._cancel = True
