# Future Features

## 1. Multi-Speaker Detection
Detect and label different speakers in the video. Each subtitle line shows who is speaking (Speaker 1, Speaker 2, or custom names). Users can assign unique styles per speaker — different colors, positions, fonts. Uses pyannote-audio for speaker diarization combined with faster-whisper timestamps.

## 2. Karaoke Word Highlight
Word-by-word highlight mode using faster-whisper's word-level timestamps. Each word lights up as it's spoken in the video preview. Useful for music videos, language learning, and social media content.

## 3. Style Presets
One-click style templates: "YouTube", "Netflix", "TikTok Bold", "Minimal", etc. Each preset configures font, size, colors, outline, background, and position. Users can also save their own custom presets.

## 4. Cloud Transcription (Local vs Cloud)
Give users a choice between local CPU (faster-whisper, free forever, ~200MB install) and cloud transcription (Groq whisper-large-v3 or OpenAI Whisper API). Cloud option includes 30 free minutes of credit. After credits are used, users enter their own Groq or OpenAI API key. Users can also choose to use their own API key from the start, bypassing the free credits.
