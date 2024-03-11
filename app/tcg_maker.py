import os
import pandas as pd
import re
      
from typing import List  
from playwright.sync_api import sync_playwright
from PIL import Image

from app.tcg_maker_io import TCGMakerIO

class TCGMaker:
    def __init__(self) -> None:
        pass

    def run(self, settings: dict) -> str:
        print("Running TCG Maker with settings: ", settings)

        csv = settings["csv"]

        if settings["preprocess_csv"] == True:
            csv = self.preprocess_csv(csv)

        card_ids: list[int]
        if settings["render_all"] == False:
            card_ids = settings["card_ids"]
            csv = csv[csv["ID"].isin(card_ids)]
            card_ids = [i for i in card_ids if i in csv["ID"].tolist()]
        else:
            card_ids = csv["ID"].tolist()

        # Read layout settings
        card_width_mm = settings["card_width_mm"]
        card_height_mm = settings["card_height_mm"]
        bleed_mm = settings["bleed_mm"]
        border_radius_mm = settings["border_radius_mm"]
        dpi = settings["dpi"]

        # Convert mm to px
        width_no_bleed_px = int(card_width_mm * dpi / 25.4)
        height_no_bleed_px = int(card_height_mm * dpi / 25.4)
        width_with_bleed_px = int((card_width_mm + 2 * bleed_mm) * dpi / 25.4)
        height_with_bleed_px = int((card_height_mm + 2 * bleed_mm) * dpi / 25.4)
        bleed_px = int(bleed_mm * dpi / 25.4)
        border_radius_px = int(border_radius_mm * dpi / 25.4)
        
        if settings["render_html"] == True:
            self.render_html(
                csv,
                html_input_path=os.path.join(settings["input_path"], "html"),
                html_output_path=os.path.join(settings["output_path"], "html"),
                width_no_bleed_px=width_no_bleed_px,
                height_no_bleed_px=height_no_bleed_px,
                width_with_bleed_px=width_with_bleed_px,
                height_with_bleed_px=height_with_bleed_px,
                bleed_px=bleed_px,
                border_radius_px=border_radius_px,
            )

        if settings["render_images"] == True:
            self.render_images(
                card_ids=list(set(card_ids)), # Remove duplicates
                html_input_path=os.path.join(settings["output_path"], "html"),
                image_output_path=os.path.join(settings["output_path"], "images"),
                width_with_bleed_px=width_with_bleed_px,
                height_with_bleed_px=height_with_bleed_px,
            )
            

        if settings["render_special"] == True:
            self.render_special(
                image_input_path=os.path.join(settings["input_path"], "images"),
                image_output_path=os.path.join(settings["output_path"], "images"),
                card_width_px=width_no_bleed_px,
                card_height_px=height_no_bleed_px,
            )

        if settings["stitch_images"] == True:
            self.stitch_images(
                image_input_path=os.path.join(settings["output_path"], "images"),
                image_output_path=os.path.join(settings["output_path"], "images"),
                card_ids=card_ids, # Keep duplicates
                card_width_px=width_no_bleed_px,
                card_height_px=height_no_bleed_px,
                stitch_x=settings["stitch_x"],
                stitch_y=settings["stitch_y"],
                dpi=dpi,
            )

        print("Done.")
        return os.path.join(settings["output_path"], "images")

    def preprocess_csv(self, old_csv: pd.DataFrame) -> pd.DataFrame:
        print("Preprocessing CSV...")
        
        # TODO: Pre-process your CSV here
        new_csv = old_csv

        return new_csv
    
    def render_html(
        self,
        csv: pd.DataFrame,
        html_input_path: str,
        html_output_path: str,
        width_no_bleed_px: int,
        height_no_bleed_px: int,
        width_with_bleed_px: int,
        height_with_bleed_px: int,
        bleed_px: int,
        border_radius_px: int,
    ) -> None:
        print("Rendering HTML...")

        # Load the CSS style file
        # TODO: This could be done by automatically finding the CSS from the HTML header.
        css = ""
        with open(
            os.path.join(html_input_path, "style.css"),
            "r",
            encoding="utf-8"
        ) as f:
            css = f.read()

        # Render the HTML
        for index, row in csv.iterrows():
            print(f"Rendering HTML for card {row['Title']}...")

            # Load the respective HTML template for the entity kind.
            entity_kind = row["Layout"]
            template_path = os.path.join(html_input_path, f"{entity_kind}.html")
            
            # If the template does not exist, skip this card.
            if not TCGMakerIO.exists(template_path):
                print(f"Template for {entity_kind} does not exist. Skipped.")
                continue

            # Read the template file.
            template = ""
            with open(
                template_path,
                "r",
                encoding="utf-8"
            ) as f:
                template = f.read()

            # Replace §Variable§s in the HTML template.
            ## Make sure the CSS is in the HTML first.
            template = template.replace("§Style§", css)
            ## Set other variables
            row["Width"] = str(width_with_bleed_px)
            row["Height"] = str(height_with_bleed_px)
            row["Bleed"] = str(bleed_px) + "px"
            row["BorderRadius"] = str(border_radius_px) + "px"
            row["EntityType"] = " ⌯ ".join(row["EntityType"].split(","))

            # Find all §Variable§s in the HTML template.
            variables = re.findall(r"§(.*?)§", template)
            # Replace the variables in the HTML template.
            for variable in variables:
                # If variable is unknown, skip it.
                if variable not in row:
                    continue
                # Otherwise, replace it.
                template = template.replace(f"§{variable}§", str(row[variable]))
            
            TCGMakerIO.write_file(
                os.path.join(html_output_path, f"{row['ID']}.html"),
                template
            )

            print(f"Rendered HTML for card {row['Title']}.")
    
    def render_images(
        self,
        card_ids: List[int],
        html_input_path: str,
        image_output_path: str,
        width_with_bleed_px: int,
        height_with_bleed_px: int,
    ) -> None:
        print("Rendering images...")

        html_files = [f"{i}.html" for i in card_ids]
        with sync_playwright() as context_manager:
            browser = context_manager.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({
                'width': width_with_bleed_px,
                'height': height_with_bleed_px
            })

            for filename in html_files:
                name = filename.split('.')[0]
                print(f"Rendering image for card {name}...")

                print(f"Going to page {os.path.join(html_input_path, f'{name}.html')}.")
                page.goto(
                    "file://" + os.path.join(html_input_path, f"{name}.html")
                )

                # Wait for all images to load
                page.wait_for_load_state("networkidle")

                page.screenshot(
                    path=os.path.join(
                        image_output_path,
                        f"{name}.png"
                    )
                )
                print(f"Rendered image for card {page.title()}.")

            browser.close()

        print("Done rendering cards.")

    def render_special(
        self,
        image_input_path: str,
        image_output_path: str,
        card_width_px: int,
        card_height_px: int,
    ) -> None:
        print("Rendering special...")

        # Load the hidden card.
        hidden_card = Image.open(os.path.join(image_input_path, "hiddencard.png"))
        # Crop the hidden card to the correct aspect ratio, centered.
        crop_height = int(hidden_card.width / card_width_px * card_height_px)
        hidden_card = hidden_card.crop(
            (
                0,
                (hidden_card.height - crop_height) // 2,
                hidden_card.width,
                (hidden_card.height - crop_height) // 2 + crop_height
            )
        )
        # Resize it to the correct size.
        hidden_card = hidden_card.resize(
            (
                card_width_px,
                card_height_px
            )
        )
        # Save the resized hidden card
        TCGMakerIO.ensure_path_exists(image_output_path)
        hidden_card.save(os.path.join(image_output_path, "hiddencard.png"))

        # Load the card back
        card_back = Image.open(os.path.join(image_input_path, "cardback.png"))
        # Crop the card back to the correct aspect ratio, centered
        crop_height = int(card_back.width / card_width_px * card_height_px)
        card_back = card_back.crop(
            (
                0,
                (card_back.height - crop_height) // 2,
                card_back.width,
                (card_back.height - crop_height) // 2 + crop_height
            )
        )
        # Resize it to the correct size
        card_back = card_back.resize(
            (
                card_width_px,
                card_height_px
            )
        )
        # Save the resized card back
        card_back.save(os.path.join(image_output_path, "cardback.png"))
    
    def stitch_images(
        self,
        image_input_path: str,
        image_output_path: str,
        card_ids: List[int],
        card_width_px: int,
        card_height_px: int,
        stitch_x: int,
        stitch_y: int,
        dpi: int,
    ) -> None:
        print("Preparing stitching cards...")

        files = [f"{i}.png" for i in card_ids]

        # Create the output image
        output_image = Image.new(
            'RGBA',
            (
                stitch_x * card_width_px,
                stitch_y * card_height_px
            ),
            (255, 255, 255, 255)
        )

        # Paste the cards into the output image
        # Reserve the last (bottom right) spot for the hidden card
        for i in range(stitch_x * stitch_y - 1):
            if i >= len(files):
                break
            print(f"Pasting card {files[i]}...")
            card = Image.open(os.path.join(image_input_path, files[i]))
            # Remove the bleed around the card and paste it into the output image
            # Crop the card to the correct aspect ratio, centered
            card = card.crop(
                (
                    (card.width - card_width_px) // 2,
                    (card.height - card_height_px) // 2,
                    (card.width - card_width_px) // 2 + card_width_px,
                    (card.height - card_height_px) // 2 + card_height_px
                )
            )
            output_image.paste(
                card,
                (
                    (i % stitch_x) * card_width_px,
                    (i // stitch_x) * card_height_px
                )
            )
            print(f"Pasted card {files[i]}.")

        # Paste the hidden card into the bottom right spot.
        print(f"Pasting hidden card...")
        output_image.paste(
            Image.open(os.path.join(image_input_path, "hiddencard.png")),
            (
                (stitch_x - 1) * card_width_px,
                (stitch_y - 1) * card_height_px
            )
        )
        print(f"Pasted hidden card.")

        # Save the output image
        output_image.save(
            os.path.join(image_output_path, "cards.png"),
            dpi=(dpi, dpi)
        )

        print("Successfully stitched cards.")