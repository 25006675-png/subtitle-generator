# CLAUDE.md

## Interaction Rules

- **Do NOT make edits unless the user explicitly asks for changes.** If the user is not using clear directive sentences (e.g., "edit this", "make the UI...", "fix this", "add..."), treat their message as a conversation — analyze, give opinions, answer questions, but do not modify any files.
- **Use the AskUserQuestion tool** to ask for clarification or the user's opinion whenever the intent or scope is unclear before proceeding with any edits.

## Progress Tracking

- **After making any Edit or Write changes**, always update `progress.md` with a concise summary of what was changed before finishing your turn.
- Format: append under the current date session header with `### <short title> — HH:MM`, `- **What**:`, `- **Why**:`, `- **How**:`, `- **Files**:` fields.
- If `progress.md` doesn't exist, create it with a `# Progress Log` header first.

## Project Info

- Entry point: `main.py`
- UI framework: CustomTkinter + tkinterdnd2
- Video backend: python-mpv (primary), VLC (fallback), OpenCV (fallback)
- Main branch: `master`
