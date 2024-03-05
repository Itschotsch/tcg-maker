import os

from app.ui.tcg_maker_ui import TCGMakerUI
from app.tcg_maker_io import TCGMakerIO

def main() -> None:
    # Initialize the TCG Maker IO
    TCGMakerIO.init(os.getcwd())
    # Create a new TCG Maker object
    ui = TCGMakerUI()
    # Run the TCG Maker program
    ui.make_window()

if __name__ == "__main__":
    main()