import sys
import tkinter as tk
from ui import BlackjackCounterUI

def main():
    root = tk.Tk()
    app = BlackjackCounterUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
