import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import SubtitleGeneratorApp


def main():
    app = SubtitleGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
