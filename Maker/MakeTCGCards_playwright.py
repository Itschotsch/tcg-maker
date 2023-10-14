# This Python script renders a set of cards for a TCG game.
# The layout of a card is defined in ./card.html.
# The data for the cards is defined in ./cards.csv.
# This notebook loads the CSV file, replaces the placeholders in the HTML file and renders the cards as PNG images into ./output/singles/[ID]_[NAME].png
# It then stitches the cards together into a single PNG image and saves it to ./output/cards.png.

dev_mode = False

# Imports
# Make sure you have done the installation beforehand:
# pip install --upgrade pip
# pip install pandas pytest-playwright
# playwright install
import os
import pandas as pd
import re
from playwright.sync_api import sync_playwright

__dir__ = os.path.dirname(__file__)

# Load the CSV file, keep "" as empty string, not NaN
df = pd.read_csv(
    os.path.join(__dir__, "input", 'cards.csv'),
    keep_default_na=False
)

# Load the HTML template
html_template = ""
with open(
    os.path.join(__dir__, "input", 'card.html'),
    'r',
    encoding='utf-8'
) as f:
    html_template = f.read()

width_mm = 63
height_mm = 88
bleed_mm = 3
border_radius_mm = 3
dpi = 300
width_px = int((width_mm + 2 * bleed_mm) * dpi / 25.4)
height_px = int((height_mm + 2 * bleed_mm) * dpi / 25.4)
bleed_px = int(bleed_mm * dpi / 25.4)
border_radius_px = int(border_radius_mm * dpi / 25.4)

# Render the cards
for index, row in df.iterrows():
    print(f"Rendering HTML for card {row['Title']}...")

    # Copy the string html_template to template so the original template is not modified
    template = html_template
    
    # Replace width, height and bleed
    template = template.replace("§Width§", str(width_px))
    template = template.replace("§Height§", str(height_px))
    template = template.replace("§Bleed§", str(bleed_px) + "px")
    template = template.replace("§BorderRadius§", str(border_radius_px) + "px")

    # Prepend all CSS URLs with the correct path
    template = template.replace('url(', 'url(../../input/images/')
    # Prepend all <img> srcs with the correct path
    template = template.replace('src="', 'src="../../input/images/')

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


# Render the HTML template to a PNG image
currentProgress = 0
totalProgress = len(df.index)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({
        'width': width_px,
        'height': height_px
    })

    for index, row in df.iterrows():
        print(f"Rendering image for card {row['Title']}...")

        page.goto(
            os.path.join(__dir__, "output/html", f"{row['ID']}_{row['Title']}.html")
        )

        page.screenshot(
            path=os.path.join(
                __dir__,
                'output/singles',
                f"{row['ID']}_{row['Title']}.png"
            )
        )
        currentProgress += 1
        print(f"Rendered image for card {page.title()}.\n{currentProgress/totalProgress*100}% done.")

        if dev_mode:
            break

    browser.close()

print("Done rendering cards.")