# This Python script renders a set of cards for a TCG game.
# The layout of a card is defined in input/*.html.
# The data for the cards is defined in input/cards.csv.
# This notebook loads the CSV file, replaces the placeholders in the HTML file and renders the cards as PNG images into output/singles/[ID]_[NAME].png
# It then stitches the cards together into a single PNG image and saves it to output/cards.png.

dev_mode = False
choose_csv = False
preprocess_csv = False
render_html = False
render_cards = False
render_special_cards = False
stitch_cards = True
stitch_cards_ids = [
    # Deck: Terra-Ignis-Angriff
    # https://www.notion.so/Test-Deck-Terra-Ignis-Angriff-762b30417c834c3b9c790c2f146c1892?pvs=4
    304, 304, 304,
    320, 320, 320,
    167, 167, 167,
    292, 292, 292,
    264, 264, 264,
    236, 236, 236,
    190, 190, 190,
    214, 214, 214,
    166, 166, 166,
    266, 266, 266,
    207, 207, 207,
    179, 179, 179,
    191, 191, 191,
    162, 162, 162,
]

width_mm = 63
height_mm = 88
bleed_mm = 3
border_radius_mm = 3
dpi = 300

stitch_x = 8
stitch_y = 6
stitch_without_bleed = True

width_no_bleed_px = int(width_mm * dpi / 25.4)
height_no_bleed_px = int(height_mm * dpi / 25.4)
width_with_bleed_px = int((width_mm + 2 * bleed_mm) * dpi / 25.4)
height_with_bleed_px = int((height_mm + 2 * bleed_mm) * dpi / 25.4)
bleed_px = int(bleed_mm * dpi / 25.4)
border_radius_px = int(border_radius_mm * dpi / 25.4)

# Imports
# Make sure you have done the installation beforehand:
# python -m pip install --upgrade pip
# pip install pandas pytest-playwright
# playwright install

import os
__dir__ = os.path.dirname(__file__)

chosen_csv = os.path.join(__dir__, "input", 'cards.csv')
if choose_csv:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    chosen_csv = filedialog.askopenfilename(
        title="Select the CSV file",
        filetypes=[("CSV files", "*.csv")]
    )

if preprocess_csv:
    import pandas as pd
    import re

    # Load the CSV file
    # Old columns: Kartenart,Name,Kartentext,Element,Kosten,⚔️,🛡️,⭕️,Kartentyp,Status,Playtesting,ID,Fraktion,Flavourtext,Decks,Created by,Artwork
    old = pd.read_csv(
        chosen_csv,
        keep_default_na=False
    )

    # New columns: ID,Layout,Title,Subtitle,Description,Artwork,EntityKind,EntityType,OffensiveStat,DefensiveStat,ShieldspellStat,FlavourText,CostElement,CostAmount,ElementalAmount
    new = pd.DataFrame(columns=[
        "ID", "Layout", "Title", "Subtitle", "Description", "Artwork", "EntityKind", "EntityType", "OffensiveStat", "DefensiveStat", "ShieldspellStat", "FlavourText", "CostElement", "CostAmount", "ElementalAmount"
    ])

    # Go through the new columns one by one and fill them with the old values, processed if necessary
    # ID: Use ID. Is x and should be x.
    new["ID"] = old["ID"]
    # Layout: Use Kartenart. Is Charakter asdf/Ereignis asdf/Legende asdf/Manifestation asdf/Ritual asdf and should be character/event/legend/manifestation/ritual
    new["Layout"] = old["Kartenart"].apply(lambda x: {
        "Charakter": "character",
        "Ereignis": "event",
        "Legende": "legend",
        "Manifestation": "manifestation",
        "Ritual": "ritual"
    }.get(x.split()[0], "") if x else "")
    # Title: Use Name. Is x,y and should be x.
    new["Title"] = old["Name"].apply(lambda x: x.split(',')[0] if x else "")
    # Subtitle: Use Name. Is x,y and should be y.
    new["Subtitle"] = old["Name"].apply(lambda x: x.split(',')[1] if len(x.split(',')) > 1 else "")
    # Description: Use Kartentext. Is x (http://someurl.com/) y (http://someotherurl.com/) z and should be x y z.
    new["Description"] = old["Kartentext"].apply(lambda x: re.sub(r'\((https?:\/\/[^)]+)\)', "", x) if x else "")
    # Artwork: Use ID. Is x and should be x.png.
    new["Artwork"] = old["ID"].apply(lambda x: f"{x}.png")
    # EntityKind: Use Kartenart. Is Charakter asdf/Ereignis asdf/Legende asdf/Manifestation asdf/Ritual asdf and should be Charakter/Ereignis/Legende/Manifestation/Ritual
    new["EntityKind"] = old["Kartenart"].apply(lambda x: x.split()[0] if x else "")
    # EntityType: Use Kartentyp. Is x asdf and should be x.
    new["EntityType"] = old["Kartentyp"].apply(lambda x: x.split()[0] if x else "")
    # OffensiveStat: Use ⚔️. Is x and should be x.
    new["OffensiveStat"] = old["⚔️"]
    # DefensiveStat: Use 🛡️. Is x and should be x.
    new["DefensiveStat"] = old["🛡️"]
    # ShieldspellStat: Use ⭕️. Is x and should be x.
    new["ShieldspellStat"] = old["⭕️"]
    # FlavourText: Use Flavourtext. Is x and should be x.
    new["FlavourText"] = old["Flavourtext"]
    # CostElement: Use Element. Is Aeris asdf/Terra asdf/Ignis asdf/Aqua asdf/Magica asdf/Ungeprägt asdf and should be Aeris/Terra/Ignis/Aqua/Magica/Unshaped
    new["CostElement"] = old["Element"].apply(lambda x: {
        "Aeris": "Aeris",
        "Terra": "Terra",
        "Ignis": "Ignis",
        "Aqua": "Aqua",
        "Magica": "Magica",
        "Ungeprägt": "Unshaped"
    }.get(x.split()[0], "") if x else "")
    # CostAmount: Use Kosten. Is x and should be x.
    new["CostAmount"] = old["Kosten"]
    # ElementalAmount: Use 1.
    new["ElementalAmount"] = 1

    # Save the new CSV file
    new.to_csv(
        os.path.join(__dir__, "input", "csv", 'cards.csv'),
        index=False
    )

if render_html:
    import pandas as pd
    import re
    
    # Load the CSV file, keep "" as empty string, not NaN
    df = pd.read_csv(
        os.path.join(__dir__, "input", "csv", 'cards.csv'),
        keep_default_na=False
    )

    # Load the CSS file
    css = ""
    with open(
        os.path.join(__dir__, "input", "html", "style.css"),
        'r',
        encoding='utf-8'
    ) as f:
        css = f.read()

    # Render the HTML
    for index, row in df.iterrows():
        print(f"Rendering HTML for card {row['Title']}...")

        # Load the HTML template. If it doesn't exist, skip
        entity_kind = row['Layout']
        template_path = os.path.join(__dir__, "input/html", f"{entity_kind}.html")
        if not os.path.exists(template_path):
            print(f"Template for {entity_kind} does not exist. Skipped.")
            continue
        template = ""
        with open(
            template_path,
            'r',
            encoding='utf-8'
        ) as f:
            template = f.read()
        
        # Replace width, height and bleed
        # template = template.replace("§Width§", str(width_with_bleed_px))
        # template = template.replace("§Height§", str(height_with_bleed_px))
        # template = template.replace("§Bleed§", str(bleed_px) + "px")
        # template = template.replace("§BorderRadius§", str(border_radius_px) + "px")

        # Make sure the CSS is in the HTML first
        template = template.replace("§Style§", css)
        # Set other variables
        row["Width"] = str(width_with_bleed_px)
        row["Height"] = str(height_with_bleed_px)
        row["Bleed"] = str(bleed_px) + "px"
        row["BorderRadius"] = str(border_radius_px) + "px"
        row["EntityType"] = " ⌯ ".join(row['EntityType'].split(','))

        # Prepend all CSS URLs with the correct path
        # template = template.replace('url(', 'url(../../input/images/')
        # Prepend all <img> srcs with the correct path
        # template = template.replace('src="', 'src="../../input/images/')

        # Make sure the EntityType(s) is a list
        # A,B,C -> A ⌯ B ⌯ C
        # template = template.replace("§EntityType§", " ⌯ ".join(row['EntityType'].split(',')))

        # Find all {{Placeholder}}s in the HTML template
        placeholders = re.findall(r"§(.*?)§", template)

        # Replace the placeholders in the HTML template
        for placeholder in placeholders:
            # if placeholder is not a key in row, skip
            if placeholder not in row:
                continue
            template = template.replace(f"§{placeholder}§", str(row[placeholder]))
        
        if not os.path.exists(os.path.join(__dir__, "output")):
            os.makedirs(os.path.join(__dir__, "output"))
        if not os.path.exists(os.path.join(__dir__, "output/html")):
            os.makedirs(os.path.join(__dir__, "output/html"))

        with open(
            os.path.join(__dir__, "output/html", f"{row['ID']}.html"),
            'w',
            encoding='utf-8'
        ) as f:
            f.write(template)

        print(f"Rendered HTML for card {row['Title']}.")

        if dev_mode:
            break


# Render the cards
# - PNG image
# - Add bleed

if render_cards:
    from playwright.sync_api import sync_playwright

    if not os.path.exists(os.path.join(__dir__, "output")):
        os.makedirs(os.path.join(__dir__, "output"))
    if not os.path.exists(os.path.join(__dir__, "output", "html")):
        os.makedirs(os.path.join(__dir__, "output", "html"))
    if not os.path.exists(os.path.join(__dir__, "output", "singles")):
        os.makedirs(os.path.join(__dir__, "output", "singles"))
    html_files = os.listdir(os.path.join(__dir__, "output/html"))
    currentProgress = 0
    totalProgress = len(html_files)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_viewport_size({
            'width': width_with_bleed_px,
            'height': height_with_bleed_px
        })

        for filename in html_files:
            name = filename.split('.')[0]
            print(f"Rendering image for card {name}...")

            page.goto(
                os.path.join(__dir__, "output/html", f"{name}.html")
            )

            page.screenshot(
                path=os.path.join(
                    __dir__,
                    'output/singles',
                    f"{name}.png"
                )
            )
            currentProgress += 1
            print(f"Rendered image for card {page.title()}.\n{currentProgress/totalProgress*100}% done.")

            if dev_mode:
                break

        browser.close()

    print("Done rendering cards.")

# Render the special cards

if render_special_cards:
    from PIL import Image
    width = width_no_bleed_px if stitch_without_bleed else width_with_bleed_px
    height = height_no_bleed_px if stitch_without_bleed else height_with_bleed_px

    # Load the hidden card
    hidden_card = Image.open(os.path.join(__dir__, "input", "layout", "hiddencard.png"))
    # Crop the hidden card to the correct aspect ratio, centered
    crop_height = int(hidden_card.width / width * height)
    hidden_card = hidden_card.crop(
        (
            0,
            (hidden_card.height - crop_height) // 2,
            hidden_card.width,
            (hidden_card.height - crop_height) // 2 + crop_height
        )
    )
    # Resize it to the correct size
    hidden_card = hidden_card.resize(
        (
            width,
            height
        )
    )
    # Save the resized hidden card
    if not os.path.exists(os.path.join(__dir__, "output", "layout")):
        os.makedirs(os.path.join(__dir__, "output", "layout"))
    hidden_card.save(os.path.join(__dir__, "output", "layout", "hiddencard.png"))

    # Load the card back
    card_back = Image.open(os.path.join(__dir__, "input", "layout", "cardback.png"))
    # Crop the card back to the correct aspect ratio, centered
    crop_height = int(card_back.width / width * height)
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
            width,
            height
        )
    )
    # Save the resized card back
    if not os.path.exists(os.path.join(__dir__, "output", "layout")):
        os.makedirs(os.path.join(__dir__, "output", "layout"))
    card_back.save(os.path.join(__dir__, "output", "layout", "cardback.png"))

# Stitch the cards together
# - single PNG image
# - stitch_x * stitch_y cards, discard any extra cards

if stitch_cards:
    from PIL import Image

    print("Preparing stitching cards...")
    # Get the list of files
    if not os.path.exists(os.path.join(__dir__, "output")):
        os.makedirs(os.path.join(__dir__, "output"))
    if not os.path.exists(os.path.join(__dir__, "output", "singles")):
        os.makedirs(os.path.join(__dir__, "output", "singles"))

    if stitch_cards_ids == []:
        files = os.listdir(os.path.join(__dir__, "output", "singles"))
        files = [f for f in files if f.endswith('.png')]
    else:
        files = [f"{i}.png" for i in stitch_cards_ids]

    # Sort the files by ID
    files = sorted(files, key=lambda f: f.split('_')[0])

    # Create the output image
    width = width_no_bleed_px if stitch_without_bleed else width_with_bleed_px
    height = height_no_bleed_px if stitch_without_bleed else height_with_bleed_px
    output_image = Image.new(
        'RGBA',
        (
            stitch_x * width,
            stitch_y * height
        ),
        (255, 255, 255, 255)
    )

    # Paste the cards into the output image
    # Reserve the last (bottom right) spot for the hidden card
    for i in range(stitch_x * stitch_y - 1):
        if i >= len(files):
            break
        print(f"Pasting card {files[i]}...")
        card = Image.open(os.path.join(__dir__, "output/singles", files[i]))
        # Remove the bleed around the card and paste it into the output image
        if stitch_without_bleed:
            card = card.crop(
                (
                    bleed_px,
                    bleed_px,
                    width_with_bleed_px - bleed_px,
                    height_with_bleed_px - bleed_px
                )
            )
        output_image.paste(
            card,
            (
                (i % stitch_x) * width,
                (i // stitch_x) * height
            )
        )
        print(f"Pasted card {files[i]}.")

    # Paste the hidden card into the bottom right spot
    print(f"Pasting hidden card...")
    if not os.path.exists(os.path.join(__dir__, "output", "layout")):
        os.makedirs(os.path.join(__dir__, "output", "layout"))
    output_image.paste(
        Image.open(os.path.join(__dir__, "output", "layout", "hiddencard.png")),
        (
            (stitch_x - 1) * width,
            (stitch_y - 1) * height
        )
    )
    print(f"Pasted hidden card.")

    # Save the output image
    output_image.save(
        os.path.join(__dir__, "output", "cards.png"),
        dpi=(dpi, dpi)
    )

    print("Successfully stitched cards.")