import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import os
from typing import Literal

from app.tcg_maker import TCGMaker
from app.tcg_maker_io import TCGMakerIO
from app.tcg_maker_util import TCGMakerUtil

class TCGMakerUI:
    
    def __init__(self) -> None:
        # Window
        ## Create a new window
        self.window = tk.Tk()
        ## Set the window title
        self.window.title("TCG Maker")
        ## Set the window size
        self.window.geometry("")
        ## Set the theme
        self.window.tk_setPalette(background="#f0f0f0", foreground="#000000", activeBackground="#4d4d4d", activeForeground="#ffffff")

        # Layout
        # - Title
        # - File picker to pick a CSV file of all cards' data
        # - Checkbox "Pre-process CSV file (necessary if it was exported from Notion)", default true
        # - Checkbox "Render HTML files (necessary if any card data changed)", default true
        # - Checkbox "Render card images (necessary if any card data changed)", default true
        # - Checkbox "Render special cards (necessary if the hidden card or the card back changed)", default true
        # - Checkbox "Stitch card images for Tabletop Simulator (necessary if any card data or special cards changed)", default true
        # - Toggle between "Render all cards" and "Render only cards with these IDs"
        # - Textbox "Card IDs" (grayed out if "Render all cards" is selected)
        # - Button "Run"

        ## Frame
        # if self.frame is not None:
        #     self.frame.pack_forget()
        self.frame = tk.Frame(self.window)
        self.frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        ## Title
        self.title_label = self.add_ui(tk.Label(self.frame, text="TCG Maker", font=("Arial", 24)))
        # self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

        ## File picker
        self.file_picker_frame = self.add_ui(
            tk.Frame(self.frame)
        )
        self.file_picker_label = self.add_ui(
            tk.Label(
                self.file_picker_frame,
                text="CSV File:"
            ),
            side=tk.LEFT
        )
        self.file_picker_entry = self.add_ui(
            tk.Entry(
                self.file_picker_frame,
                width=50
            ),
            expand=True,
            side=tk.LEFT
        )
        self.file_picker_button = self.add_ui(
            tk.Button(
                self.file_picker_frame,
                text="Browse",
                command=self.browse_csv
            ),
            side=tk.LEFT,
        )

        ## Pre-process CSV file
        self.preprocess_csv_var = tk.BooleanVar()
        self.preprocess_csv_var.set(True)
        self.preprocess_csv_checkbox = self.add_ui(
            tk.Checkbutton(
                self.frame,
                text="Pre-process CSV file (necessary if it was exported from Notion)",
                variable=self.preprocess_csv_var,
                anchor=tk.W
            )
        )

        ## Render HTML files
        self.render_html_var = tk.BooleanVar()
        self.render_html_var.set(True)
        # self.render_html_checkbox = self.add_ui(tk.Checkbutton(self.frame, text="Render HTML files (necessary if any card data changed)", variable=self.render_html_var))
        self.render_html_checkbox = self.add_ui(
            tk.Checkbutton(
                self.frame,
                text="Render HTML files (necessary if any card data changed)",
                variable=self.render_html_var,
                anchor=tk.W
            )
        )

        ## Render card images
        self.render_images_var = tk.BooleanVar()
        self.render_images_var.set(True)
        # self.render_images_checkbox = self.add_ui(tk.Checkbutton(self.frame, text="Render card images (necessary if any card data changed)", variable=self.render_images_var))
        self.render_images_checkbox = self.add_ui(
            tk.Checkbutton(
                self.frame,
                text="Render card images (necessary if any card data changed)",
                variable=self.render_images_var,
                anchor=tk.W
            )
        )

        ## Render special cards
        self.render_special_var = tk.BooleanVar()
        self.render_special_var.set(True)
        # self.render_special_checkbox = self.add_ui(tk.Checkbutton(self.frame, text="Render special cards (necessary if the hidden card or the card back changed)", variable=self.render_special_var))
        self.render_special_checkbox = self.add_ui(
            tk.Checkbutton(
                self.frame,
                text="Render special cards (necessary if the hidden card or the card back changed)",
                variable=self.render_special_var,
                anchor=tk.W
            )
        )

        ## Stitch card images for Tabletop Simulator
        self.stitch_images_var = tk.BooleanVar()
        self.stitch_images_var.set(True)
        # self.stitch_images_checkbox = self.add_ui(tk.Checkbutton(self.frame, text="Stitch card images for Tabletop Simulator (necessary if any card data or special cards changed)", variable=self.stitch_images_var))
        self.stitch_images_checkbox = self.add_ui(
            tk.Checkbutton(
                self.frame,
                text="Stitch card images for Tabletop Simulator (necessary if any card data or special cards changed)",
                variable=self.stitch_images_var,
                anchor=tk.W
            )
        )

        ## Toggle between "Render all cards" and "Render only cards with these IDs"
        self.render_all_var_frame = self.add_ui(
            tk.Frame(self.frame)
        )
        self.render_all_var = tk.BooleanVar()
        self.render_all_var.set(True)
        # self.render_all_radio = self.add_ui(tk.Radiobutton(self.frame, text="Render all cards", variable=self.render_all_var, value=True))
        # self.render_ids_radio = self.add_ui(tk.Radiobutton(self.frame, text="Render only cards with these IDs", variable=self.render_all_var, value=False))
        self.render_all_radio = self.add_ui(
            tk.Radiobutton(
                self.render_all_var_frame,
                text="Render all cards",
                variable=self.render_all_var,
                value=True,
                anchor=tk.W
            ),
            side=tk.LEFT
        )
        self.render_ids_radio = self.add_ui(
            tk.Radiobutton(
                self.render_all_var_frame,
                text="Only render cards with the following IDs",
                variable=self.render_all_var,
                value=False,
                anchor=tk.W
            ),
            side=tk.LEFT
        )

        ## Textbox "Card IDs"
        self.card_ids_entry = tk.Entry(self.frame, width=50)
        self.card_ids_entry.insert(0, "1,2,3")
        self.card_ids_entry.config(state=tk.DISABLED)
        def toggle_card_ids_entry():
            if self.render_all_var.get():
                self.card_ids_entry.config(state=tk.DISABLED)
            else:
                self.card_ids_entry.config(state=tk.NORMAL)
        self.render_all_var.trace("w", lambda *args: toggle_card_ids_entry())
        self.add_ui(
            self.card_ids_entry,
        )

        ## Button "Run"
        self.run_button = self.add_ui(
            tk.Button(
                self.frame,
                text="Run",
                command=self.run
            ),
            fill=tk.X
        )


    def add_ui(self,
        element: tk.Widget,
        padx: int = 10,
        pady: int = 10,
        fill: Literal['x'] | Literal['y'] | Literal['both'] = tk.BOTH,
        expand: bool = False,
        side: Literal['top'] | Literal['left'] = tk.TOP
    ) -> tk.Widget:
        # self.frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        element.pack(
            padx=padx,
            pady=pady,
            fill=fill,
            expand=expand,
            side=side
        )
        return element

    def start_window(self) -> None:
        # Open the window
        self.window.mainloop()

    def browse_csv(self) -> None:
        # Open a file dialog to choose a CSV file
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        # Set the file picker entry to the chosen file
        if type(self.file_picker_entry) is not tk.Entry:
            raise ValueError("file_picker_entry is not an Entry")
        self.file_picker_entry.delete(0, tk.END)
        self.file_picker_entry.insert(0, file_path)

    def run(self) -> None:
        if type(self.file_picker_entry) is not tk.Entry:
            raise ValueError("file_picker_entry is not an Entry")
        
        settings = TCGMakerUtil.complete_settings({
            "csv_file": self.file_picker_entry.get(),
            "csv": TCGMakerIO.read_csv_file(self.file_picker_entry.get()),
            "preprocess_csv": self.preprocess_csv_var.get(),
            "render_html": self.render_html_var.get(),
            "render_images": self.render_images_var.get(),
            "render_special": self.render_special_var.get(),
            "stitch_images": self.stitch_images_var.get(),
            "render_all": self.render_all_var.get(),
            "card_ids": self.card_ids_entry.get() if not self.render_all_var.get() else None,
        })
        
        # Checks
        ## CSV file
        if not os.path.exists(settings["csv_file"]):
            messagebox.showerror("Error", "The specified CSV file does not exist.")
            return
        ## Card IDs
        if not settings["render_all"]:
            try:
                settings["card_ids"] = TCGMakerUtil.parse_comma_seprarated_ints(settings["card_ids"])
            except ValueError:
                messagebox.showerror("Error", "The specified card IDs are not valid.\nUse a comma-separated list of integers.")
                return
        ## Any boxes checked
        if not any([
            settings["preprocess_csv"],
            settings["render_html"],
            settings["render_images"],
            settings["render_special"],
            settings["stitch_images"],
        ]):
            messagebox.showinfo("Info", "No action was selected.")
            return
        
        # Run the TCG Maker program
        tcg_maker:TCGMaker = TCGMaker()
        output_path = tcg_maker.run(settings)

        # Open the output folder
        os.startfile(output_path)