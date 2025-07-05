import os

import http.server
import cgi
import json

from app.tcg_maker import TCGMaker
from app.tcg_maker_io import TCGMakerIO
from app.tcg_maker_util import TCGMakerUtil

class TCGMakerWeb:
    
    def __init__(self) -> None:
        pass

    def start_web(self, ip: str | None = None, port: int | None = None) -> None:
        if ip is None:
            ip = "0.0.0.0"
        if port is None:
            port = 8000
        server_address = (ip, port)
        handler = TCGMakerHTTPRequestHandler
        httpd = http.server.HTTPServer(server_address, handler)
        print(f"Server running on {server_address[0]}:{server_address[1]}")
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

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST"}
        )

        settings = {
            "fetch_remote_csv": "csv_selection" in form and form["csv_selection"].value == "fetch",
            "provided_local_csv": "csv_selection" in form and form["csv_selection"].value == "provided",
            "csv": TCGMakerIO.read_csv_string(form["csv_file"].value.decode("utf-8")) if "csv_file" in form else None,
            "preprocess_csv": "preprocess_csv" in form and form["preprocess_csv"].value == "on",
            "render_html": "render_html" in form and form["render_html"].value == "on",
            "render_png": "render_png" in form and form["render_png"].value == "on",
            "render_special": "render_special" in form and form["render_special"].value == "on",
            # "stitch_images": "stitch_images" in form and form["stitch_images"].value == "on",
            "render_all": "render_selection" in form and form["render_selection"].value == "all",
            "render_ids": "render_selection" in form and form["render_selection"].value == "ids",
            "card_ids": TCGMakerUtil.parse_comma_seprarated_ints(form["card_ids"].value) if "card_ids" in form else None,
            # "render_pdf": "render_pdf_tts" in form and form["render_pdf_tts"].value == "pdf",
            "render_jpg": "render_jpg" in form and form["render_jpg"].value == "on",
            "render_pdf_singles": "render_pdf_singles" in form and form["render_pdf_singles"].value == "on",
            "render_pdf": "render_pdf" in form and form["render_pdf"].value == "on",
            "render_tts": "render_tts" in form and form["render_tts"].value == "on",
        }

        settings = TCGMakerUtil.complete_settings(settings)

        # Run the TCG Maker
        tcg_maker: TCGMaker = TCGMaker()

        output_paths: List[str]
        try:
            output_paths = tcg_maker.run(settings)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))
            return

        # Send the headers and return the result
        self.send_response(200)
        if len(output_paths) == 0:
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Disposition", "inline")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "No output files generated"}).encode("utf-8"))
        elif len(output_paths) == 1:
            if settings["render_pdf"]:
                self.send_header("Content-type", "application/pdf")
                self.send_header("Content-Disposition", "attachment; filename=cards.pdf")
                self.end_headers()
                with open(output_paths[0], "rb") as file:
                    self.wfile.write(file.read())
            elif settings["render_pdf_singles"]:
                self.send_header("Content-type", "application/pdf")
                self.send_header("Content-Disposition", "attachment; filename=cards_singles.pdf")
                self.end_headers()
                with open(output_paths[0], "rb") as file:
                    self.wfile.write(file.read())
            elif settings["render_tts"]:
                self.send_header("Content-type", "image/png")
                self.send_header("Content-Disposition", "attachment; filename=cards.png")
                self.end_headers()
                with open(output_paths[0], "rb") as file:
                    self.wfile.write(file.read())
            elif settings["render_jpg"]:
                self.send_header("Content-type", "application/json")
                self.send_header("Content-Disposition", "inline")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "JPG output files generated", "path": output_paths[0]}).encode("utf-8"))
            else:
                self.send_header("Content-type", "application/json")
                self.send_header("Content-Disposition", "inline")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Output files generated", "path": output_paths[0]}).encode("utf-8"))
        else:
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Disposition", "inline")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "Output files generated", "paths": output_paths}).encode("utf-8"))