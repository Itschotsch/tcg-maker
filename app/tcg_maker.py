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

        csv: pd.DataFrame
        if settings["fetch_remote_csv"] == True:
            csv = TCGMakerIO.fetch_remote_csv()
        else: # settings["provided_local_csv"] == True
            csv = settings["csv"]

        if settings["preprocess_csv"] == True:
            csv = self.preprocess_csv(csv)

        card_ids: list[int]
        if settings["render_all"] == False:
            card_ids = settings["card_ids"]
            csv = csv[csv["ID"].isin(card_ids)]
            card_ids = [i for i in card_ids if i in csv["ID"].tolist()]
        else: # settings["render_ids"] == True
            card_ids = csv["ID"].tolist()

        # Read layout settings
        card_width_no_bleed_mm = settings["card_width_mm"]
        card_height_no_bleed_mm = settings["card_height_mm"]
        bleed_mm = settings["bleed_mm"]
        card_width_with_bleed_mm = card_width_no_bleed_mm + 2 * bleed_mm
        card_height_with_bleed_mm = card_height_no_bleed_mm + 2 * bleed_mm
        border_radius_mm = settings["border_radius_mm"]
        dpi = settings["dpi"]

        # Convert mm to px
        card_width_no_bleed_px = int(card_width_no_bleed_mm * dpi / 25.4)
        card_height_no_bleed_px = int(card_height_no_bleed_mm * dpi / 25.4)
        card_width_with_bleed_px = int(card_width_with_bleed_mm * dpi / 25.4)
        card_height_with_bleed_px = int(card_height_with_bleed_mm * dpi / 25.4)
        bleed_px = int(bleed_mm * dpi / 25.4)
        border_radius_px = int(border_radius_mm * dpi / 25.4)
        
        if settings["render_html"] == True:
            self.render_html(
                csv,
                html_input_path=os.path.join(settings["input_path"], "html"),
                html_output_path=os.path.join(settings["output_path"], "html"),
                width_no_bleed_px=card_width_no_bleed_px,
                height_no_bleed_px=card_height_no_bleed_px,
                width_with_bleed_px=card_width_with_bleed_px,
                height_with_bleed_px=card_height_with_bleed_px,
                bleed_px=bleed_px,
                border_radius_px=border_radius_px,
            )

        if settings["render_png"] == True:
            self.render_png(
                card_ids=list(set(card_ids)), # Remove duplicates
                html_input_path=os.path.join(settings["output_path"], "html"),
                image_output_path=os.path.join(settings["output_path"], "images"),
                width_with_bleed_px=card_width_with_bleed_px,
                height_with_bleed_px=card_height_with_bleed_px,
            )

        if settings["render_special"] == True:
            self.render_special(
                image_input_path=os.path.join(settings["input_path"], "images"),
                image_output_path=os.path.join(settings["output_path"], "images"),
                card_width_px=card_width_no_bleed_px,
                card_height_px=card_height_no_bleed_px,
            )

        result_path = []

        # if settings["stitch_images"] == True:
        #     result_path = self.stitch_images(
        #         image_input_path=os.path.join(settings["output_path"], "images"),
        #         image_output_path=os.path.join(settings["output_path"], "images"),
        #         card_ids=card_ids, # Keep duplicates
        #         card_width_px=width_no_bleed_px,
        #         card_height_px=height_no_bleed_px,
        #         stitch_x=settings["stitch_x"],
        #         stitch_y=settings["stitch_y"],
        #         dpi=dpi,
        #     )

        if settings["render_jpg"] == True:
            result_path.append(self.convert_png_to_jpg(
                card_ids=list(set(card_ids)), # Remove duplicates
                png_input_path=os.path.join(settings["output_path"], "images"),
                jpg_output_path=os.path.join(settings["tcg_arena_path"], "images"),
                width_with_bleed_px=card_width_with_bleed_px,
                height_with_bleed_px=card_height_with_bleed_px,
                width_no_bleed_px=card_width_no_bleed_px,
                height_no_bleed_px=card_height_no_bleed_px,
            ))
        if settings["render_pdf"] == True:
            settings["stitch_x"] = 3
            settings["stitch_y"] = 3
            result_path.append(self.render_pdf(
                image_input_path=os.path.join(settings["output_path"], "images"),
                pdf_output_path=os.path.join(settings["output_path"], "images"),
                card_ids=card_ids, # Keep duplicates
                card_width_no_bleed_mm=card_width_no_bleed_mm,
                card_height_no_bleed_mm=card_height_no_bleed_mm,
                card_width_no_bleed_px=card_width_no_bleed_px,
                card_height_no_bleed_px=card_height_no_bleed_px,
                stitch_x=settings["stitch_x"],
                stitch_y=settings["stitch_y"],
                dpi=dpi,
            ))
        if settings["render_tts"] == True:
            settings["stitch_x"] = 10
            settings["stitch_y"] = 7
            result_path.append(self.stitch_images(
                image_input_path=os.path.join(settings["output_path"], "images"),
                image_output_path=os.path.join(settings["output_path"], "images"),
                card_ids=card_ids, # Keep duplicates
                card_width_px=card_width_no_bleed_px,
                card_height_px=card_height_no_bleed_px,
                stitch_x=settings["stitch_x"],
                stitch_y=settings["stitch_y"],
                dpi=dpi,
            ))

        print("Done.")
        return result_path

    def preprocess_csv(self, old_csv: pd.DataFrame) -> pd.DataFrame:
        print("Preprocessing CSV...")
        
        # Set new columns
        new_csv = pd.DataFrame(columns=[
            "ID",
            "Layout",
            "Title",
            "Subtitle",
            "Description",
            "Artwork",
            "EntityKind",
            "EntityType",
            "OffensiveStat",
            "DefensiveStat",
            "ShieldspellStat",
            "FlavourText",
            # "CostElement",
            # "CostAmount",
            "CostTerra",
            "CostAqua",
            "CostAeris",
            "CostIgnis",
            "CostMagica",
            "CostUnshaped",
            "Elemental",
            "ElementalAmount",
        ])

        # Go through the new columns one by one and fill them with the old values, processed if necessary
        # ID: Use ID. Is x and should be x.
        new_csv["ID"] = old_csv["ID"]
        # Layout: Use Kartenart. Is Charakter asdf/Ereignis asdf/Legende asdf/Manifestation asdf/Ritual asdf and should be character/event/legend/manifestation/ritual
        new_csv["Layout"] = old_csv["Kartenart"].apply(lambda x: {
            "Charakter": "character",
            "Ereignis": "event",
            "Legende": "legend",
            "Manifestation": "manifestation",
            "Ritual": "ritual"
        }.get(x.split()[0], "") if x else "")
        # Title: Use Name. Is x,y and should be x.
        new_csv["Title"] = old_csv["Name"].apply(lambda x: x.split(",")[0] if x else "")
        # Subtitle: Use Name. Is x,y and should be y.
        new_csv["Subtitle"] = old_csv["Name"].apply(lambda x: x.split(",")[1] if len(x.split(",")) > 1 else "")
        # Description: Use Kartentext.
        new_csv["Description"] = old_csv["Kartentext"].apply(
            lambda x:
                # Is <ignis/> or <ignis> and should be <ignis></ignis>
                re.sub(r"<(ignis|terra|aqua|aeris|magica|unshaped)(/?)>", r"<\1></\1>", 
                # Is x (http://someurl.com/) y (http://someotherurl.com/) z and should be x y z.
                re.sub(r"\((https?:\/\/[^)]+)\)", "", x)) if x else x
        )
        # Artwork: Use ID. Is x and should be x.png.
        new_csv["Artwork"] = old_csv["ID"].apply(lambda x: f"{x}.png")
        # EntityKind: Use Kartenart. Is Charakter asdf/Ereignis asdf/Legende asdf/Manifestation asdf/Ritual asdf and should be Charakter/Ereignis/Legende/Manifestation/Ritual
        new_csv["EntityKind"] = old_csv["Kartenart"].apply(lambda x: x.split()[0] if x else "")
        # EntityType: Use Kartentyp. Is x asdf and should be x.
        new_csv["EntityType"] = old_csv["Kartentyp"].apply(lambda x: x.split()[0] if x else "")
        # OffensiveStat: Use ⚔️. Is x and should be x.
        new_csv["OffensiveStat"] = old_csv["⚔️"]
        # DefensiveStat: Use 🛡️. Is x and should be x.
        new_csv["DefensiveStat"] = old_csv["🛡️"]
        # ShieldspellStat: Use ⭕️. Is x and should be x.
        new_csv["ShieldspellStat"] = old_csv["⭕️"]
        # FlavourText: Use Flavourtext. Is x and should be x.
        new_csv["FlavourText"] = old_csv["Flavourtext"]
        # CostElement: Use Element. Is Aeris asdf/Terra asdf/Ignis asdf/Aqua asdf/Magica asdf/Ungeprägt asdf and should be Aeris/Terra/Ignis/Aqua/Magica/Unshaped
        # new_csv["CostElement"] = old_csv["Element"].apply(lambda x: {
        #     "Aeris": "aeris",
        #     "Terra": "terra",
        #     "Ignis": "ignis",
        #     "Aqua": "aqua",
        #     "Magica": "magica",
        #     "Ungeprägt": "unshaped"
        # }.get(x.split()[0], "") if x else "")
        # CostAmount: Use Kosten. Is x and should be x.
        # new_csv["CostAmount"] = old_csv["Kosten"]
        # CostTerra: Use Kosten Terra. Is x and should be x.
        new_csv["CostTerra"] = old_csv["Kosten Terra"]
        # CostAqua: Use Kosten Aqua. Is x and should be x.
        new_csv["CostAqua"] = old_csv["Kosten Aqua"]
        # CostAeris: Use Kosten Aeris. Is x and should be x.
        new_csv["CostAeris"] = old_csv["Kosten Aeris"]
        # CostIgnis: Use Kosten Ignis. Is x and should be x.
        new_csv["CostIgnis"] = old_csv["Kosten Ignis"]
        # CostMagica: Use Kosten Magica. Is x and should be x.
        new_csv["CostMagica"] = old_csv["Kosten Magica"]
        # CostUnshaped: Use Kosten Ungeprägt. Is x and should be x.
        new_csv["CostUnshaped"] = old_csv["Kosten Ungeprägt"]
        # Elemental: Use Element. Is Aeris asdf/Terra asdf/Ignis asdf/Aqua asdf/Magica asdf/Ungeprägt asdf and should be Aeris/Terra/Ignis/Aqua/Magica/Unshaped
        new_csv["Elemental"] = old_csv["Element"].apply(lambda x: {
            "Aeris": "aeris",
            "Terra": "terra",
            "Ignis": "ignis",
            "Aqua": "aqua",
            "Magica": "magica",
            "Dunkelheit": "malice",
            "Ungeprägt": "unshaped",
        }.get(x.split()[0], "") if x else "")
        # ElementalAmount: Use 1.
        new_csv["ElementalAmount"] = 1
        # Print Element of ID 195
        print(old_csv.loc[old_csv['ID'] == 195, 'Element'].values[0])
        print(new_csv.loc[old_csv['ID'] == 195, 'Elemental'].values[0])

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
            try:
                print(f"Rendering HTML for card{' ' + row['Title'] if 'Title' in row else ''}...")

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
            except Exception as e:
                print(f"Error rendering HTML for card {row['Title']}: {e}")
    
    def render_png(
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
                try:
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
                except Exception as e:
                    print(f"Error rendering image for card {name}: {e}")

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

        # If the hidden card exists:
        if TCGMakerIO.exists(os.path.join(image_input_path, "hiddencard.png")):
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

        # If the card back exists:
        if TCGMakerIO.exists(os.path.join(image_input_path, "cardback.png")):
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
    ) -> str:
        print("Preparing stitching cards...")

        files = [f"{i}.png" for i in card_ids]

        # Create the output image
        output_image = Image.new(
            'RGB',
            (
                stitch_x * card_width_px,
                stitch_y * card_height_px
            ),
            (255, 255, 255)
        )

        # Paste the cards into the output image
        # Reserve the last (bottom right) spot for the hidden card
        for i in range(stitch_x * stitch_y - 1):
            try:
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
            except Exception as e:
                print(f"Error pasting card {files[i]}: {e}")

        # If the hidden card exists:
        if TCGMakerIO.exists(os.path.join(image_input_path, "hiddencard.png")):
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
        else:
            print("No hidden card found. Skipping.")

        # Save the output image
        result_path = os.path.join(image_output_path, "cards.png")
        output_image.save(
            result_path,
            dpi=(dpi, dpi)
        )

        print("Successfully stitched cards.")
        return result_path
    
    def convert_png_to_jpg(
        self,
        card_ids: List[int],
        png_input_path: str,
        jpg_output_path: str,
        width_with_bleed_px: int,
        height_with_bleed_px: int,
        width_no_bleed_px: int,
        height_no_bleed_px: int,
    ) -> str:
        print("Converting images to JPEGs...")

        for filename in os.listdir(png_input_path):
            if filename.endswith(".png"):
                name = filename.split('.')[0]
                # Check if the image name is a number.
                if not name.isdigit():
                    continue

                # Check if the image is in the list of cards to convert.
                if int(name) not in card_ids:
                    continue
                
                print(f"Converting image for card {name}...")

                # Load the image.
                image = Image.open(os.path.join(png_input_path, filename))

                # Crop away the bleed.
                topLeftCorner = (width_with_bleed_px - width_no_bleed_px) // 2, (height_with_bleed_px - height_no_bleed_px) // 2
                image = image.crop(
                    (
                        topLeftCorner[0],
                        topLeftCorner[1],
                        topLeftCorner[0] + width_no_bleed_px,
                        topLeftCorner[1] + height_no_bleed_px
                    )
                )

                # Convert it to JPEG.
                image = image.convert("RGB")
                # Save the JPEG.
                image.save(os.path.join(jpg_output_path, f"{name}.jpg"), "JPEG")

                print(f"Converted image for card {name}.")

        print("Done converting images to JPEGs.")

        return jpg_output_path

    def render_pdf(
        self,
        image_input_path: str,
        pdf_output_path: str,
        card_ids: List[int],
        card_width_no_bleed_mm: int,
        card_height_no_bleed_mm: int,
        card_width_no_bleed_px: int,
        card_height_no_bleed_px: int,
        stitch_x: int,
        stitch_y: int,
        dpi: int,
    ) -> str:
        from PIL import Image
        from fpdf import FPDF

        print("Preparing rendering PDF...")

        files = [f"{i}.png" for i in card_ids]

        # Make pages of stitch_x * stitch_y cards each

        pdf = FPDF()

        page_width = pdf.w
        page_height = pdf.h
        print(f"Page width: {page_width}, Page height: {page_height}")

        offset_x = (page_width - stitch_x * card_width_no_bleed_mm) // 2
        offset_y = (page_height - stitch_y * card_height_no_bleed_mm) // 2
        print(f"Offset x: {offset_x}, Offset y: {offset_y}")

        pdf.auto_page_break = False
        pdf.set_font("Arial", "", 8)
        caption_margin = 3
        caption_line_height = 4

        for i in range(len(files)):
            try:
                print(f"Stitching card {files[i]}...")
                x = i % (stitch_x * stitch_y) % stitch_x
                y = i % (stitch_x * stitch_y) // stitch_x

                if x == 0 and y == 0:
                    pdf.add_page()
                    # Add page caption:
                    pdf.set_xy(0, 0)
                    pdf.multi_cell(
                        page_width,
                        offset_y,
                        ", ".join(str(x) for x in card_ids),
                        padding=caption_margin,
                        max_line_height=caption_line_height
                    )

                # pdf.image(
                #     os.path.join(image_input_path, files[i]),
                #     x * card_width_mm,
                #     y * card_height_mm,
                #     card_width_mm,
                #     card_height_mm
                # )

                # Remove bleed around image
                print(f"Removing bleed from card {files[i]}...")
                card = Image.open(os.path.join(image_input_path, files[i]))
                card = card.crop(
                    (
                        (card.width - card_width_no_bleed_px) // 2,
                        (card.height - card_height_no_bleed_px) // 2,
                        (card.width - card_width_no_bleed_px) // 2 + card_width_no_bleed_px,
                        (card.height - card_height_no_bleed_px) // 2 + card_height_no_bleed_px
                    )
                )
                print(f"Placing card at {x * card_width_no_bleed_mm}mm, {y * card_height_no_bleed_mm}mm...")
                pdf.image(
                    card,
                    x * card_width_no_bleed_mm + offset_x,
                    y * card_height_no_bleed_mm + offset_y,
                    card_width_no_bleed_mm,
                    card_height_no_bleed_mm
                )

                print(f"Stitched card {files[i]}.")
            except Exception as e:
                print(f"Error stitching card {files[i]}: {e}")

        result_path = os.path.join(pdf_output_path, "cards.pdf")

        pdf.output(result_path, "F")

        print("Successfully rendered PDF.")
        return result_path