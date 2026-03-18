"""
Dart Scorer — entry point.
Run with: python main.py
"""
import sys
import os

# ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
