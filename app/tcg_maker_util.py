import os
from typing import List

from app.tcg_maker_io import TCGMakerIO


class TCGMakerUtil:

    @staticmethod
    def parse_comma_seprarated_ints(string: str) -> List[int]:
        # Strip all whitespace and newlines from the string
        string = "".join(string.split())
        # Split the string by commas and remove any empty strings
        ints = [x for x in string.split(",") if x]
        # Convert the strings to integers
        ints = [int(x) for x in ints]
        # Set the card IDs
        return ints
    
    @staticmethod
    def complete_settings(settings: dict) -> dict:
        settings["input_path"] = os.path.join(TCGMakerIO.pwd, "input")
        settings["output_path"] = os.path.join(TCGMakerIO.pwd, "output")
        settings["card_width_mm"] = 63
        settings["card_height_mm"] = 88
        settings["bleed_mm"] = 3
        settings["border_radius_mm"] = 3
        settings["dpi"] = 300
        settings["stitch_x"] = 8
        settings["stitch_y"] = 6

        return settings