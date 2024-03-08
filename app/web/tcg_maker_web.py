import os
import sys
import csv
from typing import Literal

import http.server
import cgi
from flask import Flask, send_file, request
from flask_restful import Resource, Api
from PIL import Image
import zipfile
import io
import json
import pandas as pd
from io import StringIO

from app.tcg_maker import TCGMaker
from app.tcg_maker_io import TCGMakerIO
from app.tcg_maker_util import TCGMakerUtil

class TCGMakerWeb:
    
    def __init__(self) -> None:
        pass

    def start_web(self) -> None:
        server_address = ("", 8000)
        handler = TCGMakerHTTPRequestHandler
        httpd = http.server.HTTPServer(server_address, handler)
        print("Server running on port 8000")
        httpd.serve_forever()

class TCGMakerHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    # GET: / - Display the form to run the TCG Maker
    # POST: /api/run - Run the TCG Maker and return the result

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # Return the tcg_maker_web.html file
        with open("app/web/tcg_maker_web.html", "r") as file:
            self.wfile.write(file.read().encode("utf-8"))

    def do_POST(self) -> None:

        ctype, pdict = cgi.parse_header(self.headers.get("Content-type") or "")

        if not ctype == "multipart/form-data":
            print("Bad request")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Bad request")
            return
        
        print("Processing form data")

        self.send_response(200)
        # self.send_header("Content-type", "application/zip")
        self.send_header("Content-type", "image/png")
        self.send_header("Content-Disposition", "attachment; filename=cards.png")
        # self.send_header("Content-type", "text/plain")
        self.end_headers()

        # Form data field names:
        # - csv_file: File
        # - preprocess_csv: Checkbox
        # - render_html: Checkbox
        # - render_images: Checkbox
        # - render_special: Checkbox
        # - stitch_images: Checkbox
        # - render_all: Radio
        # - render_ids: Radio
        # - card_ids: Text
        
        # EXAMPLE:
        # Field: render_all -> on
        # Field: render_html -> on
        # Field: render_special -> on
        # Field: preprocess_csv -> on
        # Field: csv_file -> b'\xef\xbb\xbfKartenart,Name,Kartentext,Element,Kosten,\xe2\x9a\x94\xef\xb8\x8f,\xf0\x9f\x9b\xa1\xef\xb8\x8f,\xe2\xad\x95\xef\xb8\x8f,Kartentyp,Status,Playtesting,ID,Fraktion,Flavourtext,Decks,Created by,Artwork\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Wei\xc3\x9fer Greif,"Wenn der Wei\xc3\x9fe Greif stirbt, kehrt er stattdessen auf Deine Hand zur\xc3\xbcck.",Aeris (https://www.notion.so/Aeris-5996f3899d7740fc809fe30a652d20c6?pvs=21),7,35,20,,Ungeheuer (https://www.notion.so/Ungeheuer-ea8dd894ff144b2681751cf979fbde0e?pvs=21),Playtest,,3,,,,Timon,\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Heulende Eulen,sofort (https://www.notion.so/sofort-9c56f076fccf4157b07459dd557d86d7?pvs=21) spielbar.,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),2,10,10,,Wildtier (https://www.notion.so/Wildtier-566a219b7ef049469e5743f0e8b351de?pvs=21),Playtest,,4,,"Niemand sah sie kommen, denn alle blickten gen Himmel.",Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Jan Appel,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._hooting_owl_on_tree_by_Titus_Lunter_mtg_wallpaper_forest__9a89ce6b-c870-4507-a6b7-0cc11223d27b.png\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Korporal Langhorn,Alle deine W\xc3\xb6lfe Bjarturs haben +10 \xe2\x9a\x94\xef\xb8\x8f und +15 \xf0\x9f\x9b\xa1\xef\xb8\x8f.,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),4,20,20,,Krieger (https://www.notion.so/Krieger-86700da5b47d4073ae8e37cc896f9162?pvs=21),Playtest,,5,,,,Jan Appel,\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Baums\xc3\xa4ngerin Betula,Tribute diese Karte; Rufe ein [7] oder weniger \xe2\x80\x9cBesungener Baum\xe2\x80\x9d aus dem Deck.,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),4,35,30,,,Backup,f\xc3\xbcr sp\xc3\xa4ter,8,Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21),,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._celtic_shaman_sorceress_singing_black_hair_magical_scener_4c55d035-e200-44b0-aee3-0375ab0d96d7.png\r\nEreignis (https://www.notion.so/Ereignis-88e179fa1fd740499a32ee3ed4377596?pvs=21),Lieblicher Lautenklang der Baums\xc3\xa4ngerinnen,Suche einen Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21) Charakter,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),2,,,,,Backup,,9,Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21),,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._harp_forest_background_fantasy_concept_art_magic_the_gath_d438ac21-7fe1-4151-b8de-0a41c2369229.png\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Baums\xc3\xa4ngerin Tilia,Tribute diese Karte; Rufe ein [8] oder weniger \xe2\x80\x9cBesungener Baum\xe2\x80\x9d aus dem Deck.,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),5,45,30,,,Backup,f\xc3\xbcr sp\xc3\xa4ter,12,Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21),,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._celtic_shaman_barbarian_sorceress_elf_singing_red_hair_ma_40f3759a-a129-42cc-b94a-65bb78a7ffe5.png\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Baums\xc3\xa4ngerin Abies,Falls diese Karte auf den Friedhof gelegt wird; Rufe ein \xe2\x80\x9cBesungener Baum\xe2\x80\x9d von deinem Friedhof (Einmal pro Spielzug),Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),4,35,20,,,Backup,,13,Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21),,,Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._celtic_shaman_barbarian_sorceress_elf_singing_red_hair_ma_a9278542-fe50-46f4-be5f-1eed3f953a60.png\r\nEreignis (https://www.notion.so/Ereignis-88e179fa1fd740499a32ee3ed4377596?pvs=21),Heiterer Lautenklang der Baums\xc3\xa4ngerinnen,Suche einen Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21) Charakter,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),3,,,,,Backup,,14,Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21),,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._harp_forest_background_fantasy_concept_art_magic_the_gath_4e621d90-bc0f-406d-8992-11abe88e0004.png\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Baums\xc3\xa4ngerin Larix,Tribute diese Karte; Rufe ein [6] oder weniger \xe2\x80\x9cBesungener Baum\xe2\x80\x9d aus dem Deck.,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),4,30,30,,,Backup,f\xc3\xbcr sp\xc3\xa4ter,15,Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21),,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._celtic_shaman_sorceress_singing_brown_hair_magical_scener_60872445-330f-4be8-bb49-b4ff54b07aba.png\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Besungener Baum Fagus,Alle verb\xc3\xbcndeten Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21)  und Wildtier (https://www.notion.so/Wildtier-566a219b7ef049469e5743f0e8b351de?pvs=21)  Kosten 1 Element weniger um sie zu rufen,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),6,0,55,,,Backup,,16,Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21),,,Timon,\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Besungener Baum Carpinus,Bezahle 2 Terra; Zerst\xc3\xb6re einen Charakter (Einmal 
        # pro Spielzug),Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),10,0,85,,,Backup,,17,Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21),,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._ancient_mighty_tree_emerging_from_forest_low_camera_angle_7f601446-88af-4256-b974-e2fafe89e466.png\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Besungener Baum Aesculus,Um den Effekt einer Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21) zu aktiveren kannst du anstelle sie als Tribut anzubieten 2 Terra bezahlen,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),6,0,55,,,Backup,,18,Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21),,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._ancient_mighty_fir_tree_emerging_from_forest_low_camera_a_a5e395e9-e34a-40b7-8f0d-031ee03a908b.png\r\nEreignis (https://www.notion.so/Ereignis-88e179fa1fd740499a32ee3ed4377596?pvs=21),Sch\xc3\xbctzender Lautenklang der Baums\xc3\xa4ngerinnen,Bis zum Ende dieses Spielzugs: eine Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21) oder ein \xe2\x80\x9cBesungener Baum\xe2\x80\x9d ist von Karteneffekten unber\xc3\xbchrt und kann nicht zerst\xc3\xb6rt werden,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),2,,,,,Backup,,19,Baums\xc3\xa4ngerin (https://www.notion.so/Baums-ngerin-af7ba6f57aba4f63b5ceb62076cff89a?pvs=21),,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._harp_forest_background_fantasy_concept_art_magic_the_gath_6fdf1d76-b208-415c-a121-d6e2b203165a.png\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Bestie aus 
        # dem Wald,ersch (https://www.notion.so/ersch-0e02f231f9ed4e67bd55eada1e50b09e?pvs=21)einen. Zerst\xc3\xb6re einen Charakter auf dem Feld,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),7,50,10,,,Backup,,20,,,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._angry_deer_in_forest_character_art_by_Titus_Lunter_and_Pa_62bf456d-1f94-45d7-806d-287efa848cbe.png\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Brauner Hirsch,,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),4,45,35,,,Backup,,21,,,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._deer_in_forest_by_Titus_Lunter_mtg_wallpaper_green_trees__28801dd7-fc87-4e3e-82fb-66578f78deb0.png\r\nCharakter (https://www.notion.so/Charakter-cdfda7ca52aa435bbb22610007798d2f?pvs=21),Rasender B\xc3\xa4r,,Terra (https://www.notion.so/Terra-a6762ab5136d4598aafb8d77da6be70f?pvs=21),6,60,55,,,Backup,,22,,,Starterdeck Terra (https://www.notion.so/Starterdeck-Terra-200f435487934141a36042450b2b0db3?pvs=21),Timon,Alle%20Karten%2070ddd0aaafb74f56b205e643b0901290/wia._bear_in
        # Field: render_images -> on
        # Field: stitch_images -> on

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST"}
        )

        for field in form:
            print(f"Field: {field} -> {form[field].value}")
            # self.wfile.write(f"Field: {field} -> {form[field].value}\n".encode("utf-8"))

        settings = {
            "csv": TCGMakerIO.read_csv_string(form["csv_file"].value.decode("utf-8")),
            "preprocess_csv": "preprocess_csv" in form and form["preprocess_csv"].value == "on",
            "render_html": "render_html" in form and form["render_html"].value == "on",
            "render_images": "render_images" in form and form["render_images"].value == "on",
            "render_special": "render_special" in form and form["render_special"].value == "on",
            "stitch_images": "stitch_images" in form and form["stitch_images"].value == "on",
            "render_all": "render_selection" in form and form["render_selection"].value == "all",
            "render_ids": "render_selection" in form and form["render_selection"].value == "ids",
            "card_ids": TCGMakerUtil.parse_comma_seprarated_ints(form["card_ids"].value) if "card_ids" in form else None,
        }

        for field in settings:
            print(f"{field}: {settings[field]}")

        settings = TCGMakerUtil.complete_settings(settings)

        # self.wfile.write(b"asdf")
        # Run the TCG Maker
        tcg_maker = TCGMaker()
        output_path = tcg_maker.run(settings)

        # Return the result: os.path.join(output_path, "cards.png")
        with open(os.path.join(output_path, "cards.png"), "rb") as file:
            self.wfile.write(file.read())
        