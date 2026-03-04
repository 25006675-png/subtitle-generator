import sys
import os

# Ensure project root is on path
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

# Add project root to PATH so Windows can find libmpv-2.dll next to main.py
os.environ["PATH"] = _project_root + os.pathsep + os.environ.get("PATH", "")

from app.app import SubtitleGeneratorApp


def main():
    app = SubtitleGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
