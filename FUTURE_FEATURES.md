# Future Features

## 1. Multi-Speaker Detection
Detect and label different speakers in the video. Each subtitle line shows who is speaking (Speaker 1, Speaker 2, or custom names). Users can assign unique styles per speaker — different colors, positions, fonts. Uses pyannote-audio for speaker diarization combined with faster-whisper timestamps.

## 2. Karaoke Word Highlight
Word-by-word highlight mode using faster-whisper's word-level timestamps. Each word lights up as it's spoken in the video preview. Useful for music videos, language learning, and social media content.

## 3. Style Presets
One-click style templates: "YouTube", "Netflix", "TikTok Bold", "Minimal", etc. Each preset configures font, size, colors, outline, background, and position. Users can also save their own custom presets.

## 4. Cloud Transcription (Local vs Cloud)
Give users a choice between local CPU (faster-whisper, free forever, ~200MB install) and cloud transcription (Groq whisper-large-v3 or OpenAI Whisper API). Cloud option includes 30 free minutes of credit. After credits are used, users enter their own Groq or OpenAI API key. Users can also choose to use their own API key from the start, bypassing the free credits.

SHIPPING
  The Cleanest One-Click Approach
                                                                                                             
  PyInstaller bundles your Python app + all pip packages into a .exe. You just don't include mpv-2.dll.      
  Instead, on first launch, your app auto-downloads it directly from mpv's official GitHub releases:

  # On startup, if mpv not found:
  def _ensure_mpv():
      dll_path = Path(__file__).parent / "mpv-2.dll"
      if dll_path.exists():
          return True
      # Show a small dialog: "Downloading mpv for smooth playback..."
      # Download from official mpv GitHub releases directly to app folder
      # User gets it from the source, not from you

  Why this works legally: YOU never distribute the GPL binary. The user's machine fetches it directly from   
  the official source. Your app just facilitates it — same pattern used by Steam, VLC plugins, browser codec 
  downloads, etc.

  ---
  Realistic Packaging Stack

  ┌───────────────────┬──────────────────────────────────────────────────────────┐
  │       Tool        │                       What it does                       │
  ├───────────────────┼──────────────────────────────────────────────────────────┤
  │ PyInstaller       │ Bundles Python + pip packages → single .exe or folder    │
  ├───────────────────┼──────────────────────────────────────────────────────────┤
  │ Inno Setup        │ Wraps that into a proper Windows installer with one .exe │
  ├───────────────────┼──────────────────────────────────────────────────────────┤
  │ Runtime mpv fetch │ App downloads mpv-2.dll on first run if missing          │
  └───────────────────┴──────────────────────────────────────────────────────────┘

  Users see: download one .exe installer → run it → app opens → if no mpv, a small progress bar downloads it 
  → done.

  ---
  What About Other Heavy Dependencies?

  Your app has some big ones (torch, faster-whisper, pyannote). PyInstaller will bundle them but your        
  installer could be 500MB–2GB. Two options:

  1. Bundle everything — big download, works offline, simplest UX
  2. Lazy install — ship a small installer, download heavy ML models on first use (what most AI apps do —    
  Whisper does this natively already)

  Option 2 is what most production AI desktop apps do. Small installer, downloads models when the user first 
  transcribes.

  ---
  Short answer: Not complex. PyInstaller + Inno Setup + runtime mpv fetch = professional one-click experience
   with zero GPL headache.


     If you want to keep your app closed-source or MIT/Apache, you need to drop python-mpv entirely and instead:

  1. Download mpv.exe at setup time
  2. Launch it as a subprocess embedded into your Tkinter window using --wid (window ID)
  3. Control it via mpv's JSON IPC over a named pipe

  # mpv embedded in your window, controlled via IPC
  process = subprocess.Popen([
      "mpv.exe",
      f"--wid={hwnd}",          # embed video in your window
      "--input-ipc-server=\\\\.\\pipe\\mpvsocket",
      "--idle", "--pause",
      "--no-osc", "--no-input-default-bindings"
  ])

  # Control via JSON IPC
  pipe.write('{"command": ["set_property", "pause", false]}\n')
  pipe.write('{"command": ["seek", 30.5, "absolute"]}\n')

  This is exactly what many commercial apps do — Jellyfin desktop, some video editors, etc.

  ---
  Honest Summary

  - Want simplest code, don't mind GPL → python-mpv + mpv-2.dll download, release under GPLv3
  - Want to keep your license free → subprocess mpv.exe + JSON IPC, more code but legally clean
  - Don't care about smooth video right now → stick with the OpenCV fallback, ship it, revisit later

  The subprocess IPC approach is more work but it's the professional path if you ever want to monetize. Worth
   deciding your licensing intent before building further.

