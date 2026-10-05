import os
import shutil
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import pandas as pd

import config
from model import PoultryClassifier
from audio_player import play_sound_async
import server


class Application:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Industrial Vision Inspector")
        self.root.state("zoomed")

        self.classifier = PoultryClassifier(config.CLASS_NAMES)
        self.input_folder = config.DEFAULT_INPUT_FOLDER
        self.output_folder = config.DEFAULT_OUTPUT_FOLDER
        self.wrong_folder = config.DEFAULT_WRONG_FOLDER
        self.offline_mode = False
        self.stop_worker_event = threading.Event()
        self.processed_images = set()

        self.image_log = []
        self.log_file_path = self.output_folder / "prediction_log.xlsx"
        self._init_excel_log()

        for folder in [self.input_folder, self.output_folder, self.wrong_folder]:
            folder.mkdir(parents=True, exist_ok=True)

        self._build_ui()
        self._update_clock()

    def _init_excel_log(self):
        """Initializes the prediction log spreadsheet if it does not exist."""
        self.log_columns = ["Timestamp", "Image", "Prediction", "Confidence"]
        if not self.log_file_path.exists():
            df = pd.DataFrame(columns=self.log_columns)
            try:
                df.to_excel(self.log_file_path, index=False)
            except Exception as e:
                print(f"[Excel] Initialization error: {e}")

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.main_frame = ttk.Frame(notebook)
        notebook.add(self.main_frame, text="Dashboard")

        self.main_frame.columnconfigure(0, weight=3)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.columnconfigure(2, weight=2)
        self.main_frame.rowconfigure(1, weight=1)

        # Top Bar
        top_frame = ttk.Frame(self.main_frame)
        top_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=15)
        top_frame.columnconfigure(1, weight=1)

        logo_path = config.LOGO_FOLDER / "logo.png"
        if logo_path.exists():
            img = Image.open(logo_path).resize((140, 70))
            self.logo_img = ImageTk.PhotoImage(img)
            ttk.Label(top_frame, image=self.logo_img).grid(row=0, column=0, sticky='w')

        self.clock_label = ttk.Label(top_frame, font=("Helvetica", 16, "bold"))
        self.clock_label.grid(row=0, column=2, sticky='e')

        ip_panel = ttk.Frame(top_frame)
        ip_panel.grid(row=1, column=0, columnspan=3, sticky="w", pady=(10, 0))

        ttk.Label(ip_panel, text="Raspberry Pi IP:").pack(side="left", padx=(0, 5))
        self.ip_entry = ttk.Entry(ip_panel, width=18)
        self.ip_entry.insert(0, config.DEFAULT_RASPBERRY_IP)
        self.ip_entry.pack(side="left", padx=5)

        self.btn_mode = tk.Button(
            ip_panel, text="Mode: Online (Socket Active)", bg="#007bff", fg="white",
            font=("Helvetica", 9, "bold"), command=self._toggle_mode
        )
        self.btn_mode.pack(side="left", padx=10)

        # Left Panel: Data Table
        self.tree = ttk.Treeview(
            self.main_frame,
            columns=("Time", "Image", "Prediction", "Confidence"),
            show="headings"
        )
        self.tree.heading("Time", text="Timestamp")
        self.tree.heading("Image", text="Image File")
        self.tree.heading("Prediction", text="Prediction")
        self.tree.heading("Confidence", text="Confidence")

        self.tree.column("Time", width=120)
        self.tree.column("Image", width=200)
        self.tree.column("Prediction", width=120, anchor="center")
        self.tree.column("Confidence", width=90, anchor="center")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(20, 0), pady=10)

        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 15), pady=10)
        self.tree.config(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Right Panel: Preview
        preview_frame = ttk.LabelFrame(self.main_frame, text="Live Preview")
        preview_frame.grid(row=1, column=2, sticky="nsew", padx=(0, 20), pady=10)

        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(pady=20)

        self.pred_label = tk.Label(preview_frame, text="Awaiting Model...", font=("Helvetica", 14, "bold"))
        self.pred_label.pack(pady=10)

        self.btn_wrong = ttk.Button(
            preview_frame, text="Mark as Incorrect", state="disabled", command=self._mark_as_wrong
        )
        self.btn_wrong.pack(pady=15)

        # Bottom Bar: Controls
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=15)

        ttk.Button(btn_frame, text="Load Model (.pth)", command=self._choose_model).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Input Folder", command=self._set_input_folder).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Output Folder", command=self._set_output_folder).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Incorrect Folder", command=self._set_wrong_folder).pack(side="left", padx=5)

        self.btn_start = tk.Button(
            btn_frame, text="Start", bg="#28a745", fg="white",
            font=("Helvetica", 10, "bold"), command=self._start_processing
        )
        self.btn_start.pack(side="left", padx=(20, 5))

        self.btn_stop = tk.Button(
            btn_frame, text="Stop", bg="#dc3545", fg="white",
            font=("Helvetica", 10, "bold"), state="disabled", command=self._stop_processing
        )
        self.btn_stop.pack(side="left", padx=5)

    def _update_clock(self):
        self.clock_label.config(text=time.strftime("%H:%M:%S | %Y-%m-%d"))
        self.root.after(1000, self._update_clock)

    def _toggle_mode(self):
        self.offline_mode = not self.offline_mode
        if self.offline_mode:
            self.btn_mode.config(text="Mode: Offline (Folder Watch)", bg="#6c757d")
            self.ip_entry.config(state="disabled")
        else:
            self.btn_mode.config(text="Mode: Online (Socket Active)", bg="#007bff")
            self.ip_entry.config(state="normal")

    def _choose_model(self):
        path = filedialog.askopenfilename(
            title="Select Model Checkpoint",
            filetypes=[("PyTorch Models", "*.pth *.pt")]
        )
        if path:
            try:
                self.classifier.load_weights(path)
                messagebox.showinfo("Success", "Model weights loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load model:\n{e}")

    def _set_input_folder(self):
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder = Path(folder)

    def _set_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = Path(folder)
            self.log_file_path = self.output_folder / "prediction_log.xlsx"
            self._init_excel_log()

    def _set_wrong_folder(self):
        folder = filedialog.askdirectory(title="Select Target Folder for Incorrect Classifications")
        if folder:
            self.wrong_folder = Path(folder)

    def _start_processing(self):
        if not self.classifier.is_loaded():
            messagebox.showwarning("Model Required", "Please load a model checkpoint before starting.")
            return

        self.stop_worker_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.btn_wrong.config(state="normal")

        threading.Thread(target=self._worker_loop, daemon=True).start()

    def _stop_processing(self):
        self.stop_worker_event.set()
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.btn_wrong.config(state="disabled")

    def _worker_loop(self):
        server_socket = None
        if not self.offline_mode:
            server_socket = server.start_server(config.IMAGE_PORT)

        while not self.stop_worker_event.is_set():
            if not self.offline_mode and server_socket:
                server.receive_image(server_socket, self.input_folder)

            if self.input_folder.exists():
                valid_exts = {".jpg", ".jpeg", ".png"}
                files = [f for f in self.input_folder.iterdir() if f.suffix.lower() in valid_exts]
                new_files = [f for f in files if f.name not in self.processed_images]

                for img_path in new_files:
                    try:
                        pred, conf = self.classifier.predict(img_path)
                    except Exception:
                        continue

                    self.root.after(0, self._handle_prediction_ui, img_path, pred, conf)
                    self._append_to_excel(img_path.name, pred, conf)

                    if not self.offline_mode:
                        ip = self.ip_entry.get().strip()
                        if ip:
                            server.send_result_to_raspberry(ip, config.SEND_BACK_PORT, pred)

                    self.processed_images.add(img_path.name)

            time.sleep(0.3)

        if server_socket:
            server_socket.close()

    def _append_to_excel(self, image_name: str, pred: str, conf: float):
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        new_row = pd.DataFrame([{
            "Timestamp": ts,
            "Image": image_name,
            "Prediction": pred,
            "Confidence": round(conf, 4)
        }])
        try:
            if self.log_file_path.exists():
                existing_df = pd.read_excel(self.log_file_path)
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            else:
                updated_df = new_row
            updated_df.to_excel(self.log_file_path, index=False)
        except Exception as e:
            print(f"[Excel Log] Write error: {e}")

    def _handle_prediction_ui(self, img_path: Path, pred: str, conf: float):
        ts = time.strftime('%H:%M:%S')
        self.tree.insert("", tk.END, values=(ts, img_path.name, pred, f"{conf:.2f}"))
        self.tree.yview_moveto(1)

        self.image_log.append((ts, img_path, pred, conf))
        self._show_preview(img_path, pred, conf)

    def _show_preview(self, img_path: Path, pred: str, conf: float):
        if not img_path.exists():
            return

        img = Image.open(img_path)
        img.thumbnail((450, 260))
        self.current_preview_img = ImageTk.PhotoImage(img)
        self.preview_label.config(image=self.current_preview_img)

        color = "#28a745" if conf >= 0.75 else ("#fd7e14" if conf >= 0.5 else "#dc3545")
        self.pred_label.config(text=f"{pred} ({conf:.2f})", fg=color)

        sound_file = config.SOUND_MAP.get(pred)
        if sound_file:
            play_sound_async(config.SOUND_FOLDER / sound_file)

    def _on_tree_select(self, event):
        selected_id = self.tree.focus()
        if not selected_id:
            return
        vals = self.tree.item(selected_id, "values")
        if vals:
            ts, name, _, _ = vals
            for log_ts, full_path, l_pred, l_conf in self.image_log:
                if log_ts == ts and full_path.name == name:
                    self._show_preview(full_path, l_pred, l_conf)
                    break

    def _mark_as_wrong(self):
        selected_id = self.tree.focus()
        if not selected_id:
            messagebox.showinfo("Selection Required", "Please select an entry from the list.")
            return

        vals = self.tree.item(selected_id, "values")
        ts, name, _, _ = vals
        for log_ts, full_path, _, _ in self.image_log:
            if log_ts == ts and full_path.name == name:
                dest = self.wrong_folder / full_path.name
                shutil.copy(full_path, dest)
                messagebox.showinfo("Moved", f"Image copied to error directory:\n{dest.name}")
                return


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()