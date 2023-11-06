# This Python script renders a set of cards for a TCG game.
# The layout of a card is defined in input/*.html.
# The data for the cards is defined in input/cards.csv.
# This notebook loads the CSV file, replaces the placeholders in the HTML file and renders the cards as PNG images into output/singles/[ID]_[NAME].png
# It then stitches the cards together into a single PNG image and saves it to output/cards.png.

dev_mode = False
render_html = True
render_cards = True
render_special_cards = True
stitch_cards = True

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

if render_html:
    import pandas as pd
    import re
    
    # Load the CSV file, keep "" as empty string, not NaN
    df = pd.read_csv(
        os.path.join(__dir__, "input", 'cards.csv'),
        keep_default_na=False
    )

    # Render the HTML
    for index, row in df.iterrows():
        print(f"Rendering HTML for card {row['Title']}...")

        # Load the HTML template. If it doesn't exist, skip
        entity_kind = row['EntityKind']
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
        template = template.replace("§Width§", str(width_with_bleed_px))
        template = template.replace("§Height§", str(height_with_bleed_px))
        template = template.replace("§Bleed§", str(bleed_px) + "px")
        template = template.replace("§BorderRadius§", str(border_radius_px) + "px")

        # Prepend all CSS URLs with the correct path
        # template = template.replace('url(', 'url(../../input/images/')
        # Prepend all <img> srcs with the correct path
        # template = template.replace('src="', 'src="../../input/images/')

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
            os.path.join(__dir__, "output/html", f"{row['ID']}_{row['Title']}.html"),
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
    hidden_card = Image.open(os.path.join(__dir__, "input", "hiddencard.png"))
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
    hidden_card.save(os.path.join(__dir__, "output", "hiddencard.png"))

    # Load the card back
    card_back = Image.open(os.path.join(__dir__, "input", "cardback.png"))
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
    card_back.save(os.path.join(__dir__, "output", "cardback.png"))

# Stitch the cards together
# - single PNG image
# - stitch_x * stitch_y cards, discard any extra cards

if stitch_cards:
    from PIL import Image

    print("Preparing stitching cards...")
    # Get the list of files
    files = os.listdir(os.path.join(__dir__, "output/singles"))
    files = [f for f in files if f.endswith('.png')]

    # Sort the files by ID
    files = sorted(files, key=lambda f: int(f.split('_')[0]))

    # Create the output folder if it doesn't exist
    if not os.path.exists(os.path.join(__dir__, "output")):
        os.makedirs(os.path.join(__dir__, "output"))

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
    output_image.paste(
        Image.open(os.path.join(__dir__, "output", "hiddencard.png")),
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