import os
import sys

from app.tcg_maker_io import TCGMakerIO

def start_gui() -> None:
    from app.ui.tcg_maker_ui import TCGMakerUI
    # Initialize the TCG Maker IO
    TCGMakerIO.init(os.getcwd())
    # Create a new TCG Maker object
    ui = TCGMakerUI()
    # Run the TCG Maker program
    ui.start_window()

def start_web() -> None:
    from app.web.tcg_maker_web import TCGMakerWeb
    # Initialize the TCG Maker IO
    TCGMakerIO.init(os.getcwd())
    # Create a new TCG Maker object
    ui = TCGMakerWeb()
    # Run the TCG Maker program
    ui.start_web()

if __name__ == "__main__":
    # if --gui flag is passed, start the GUI
    if "--gui" in sys.argv:
        start_gui()
        sys.exit(0)
    elif "--web" in sys.argv:
        start_web()
        sys.exit(0)
    else:
        print("Usage: python main.py [--gui | --web]")
        print("  --gui: Start the TCG Maker GUI")
        print("  --web: Start the TCG Maker Web App")
        sys.exit(0)