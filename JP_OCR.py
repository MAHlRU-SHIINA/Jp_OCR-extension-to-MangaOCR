import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import numpy as np
import threading
import sys

# ==============================================================================
# === CHOOSE YOUR OCR ENGINE ===
# 'manga-ocr': Best for manga. Higher accuracy for Japanese. (RECOMMENDED)
# 'paddle': General purpose. Faster but less accurate for manga.
OCR_ENGINE = 'manga-ocr'
# ==============================================================================

# Helper function to find bundled resources (like the icon)
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
    
# <<< UI COLORS >>>
BG_COLOR = '#282a36'
FG_COLOR = '#f8f8f2'
FRAME_COLOR = '#44475a'
BTN_COLOR = '#6272a4'       # Blue Button color
BTN_ACTIVE = '#50fa7b'      # Green Active/Hover color
TEXT_BG = '#21222c'
BORDER_COLOR = '#6272a4'
RED_TEXT = '#ff5555'        # A bright red for the label
LEGENDS = ['"":', '():', '[]:', '//:', '::', 'OT:', 'ST:', 'Sfx:', 'none']

class JPOCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title('JP OCR - Loading Engine...')
        self.root.configure(bg=BG_COLOR)
        
        try:
            self.root.iconbitmap(resource_path('icon.ico'))
        except tk.TclError:
            print("Could not find or load icon.ico")
        
        self.image_paths = []
        self.img_idx = 0
        self.zoom = 1.0
        self.start_x = self.start_y = None
        self.rect = None
        self.tk_img = None
        self.current_image = None
        self.offset = (0, 0)
        self.page_counter = 1
        
        self.ocr_engine = None
        self.selected_legend = tk.StringVar(value=LEGENDS[0])

        self._setup_styles()
        self._setup_ui()
        
        threading.Thread(target=self._load_ocr, daemon=True).start()

    def _setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TCombobox', 
                        fieldbackground=BTN_COLOR, 
                        background=BTN_COLOR, 
                        foreground=FG_COLOR, 
                        selectbackground=TEXT_BG, 
                        selectforeground=BTN_ACTIVE, 
                        arrowcolor=FG_COLOR)
        style.map('TCombobox', fieldbackground=[('readonly', BTN_COLOR)])

        style.configure('TPanedwindow', background=BG_COLOR)
        style.configure('TFrame', background=BG_COLOR)

    def _load_ocr(self):
        try:
            if OCR_ENGINE == 'manga-ocr':
                from manga_ocr import MangaOcr
                self.ocr_engine = MangaOcr()
                print("Manga-OCR loaded successfully.")
            elif OCR_ENGINE == 'paddle':
                from paddleocr import PaddleOCR
                self.ocr_engine = PaddleOCR(use_textline_orientation=True, lang='japan')
                print("PaddleOCR loaded successfully.")
            else:
                raise ValueError(f"Unknown OCR_ENGINE: {OCR_ENGINE}")
                
            self.root.title(f'JP OCR - {OCR_ENGINE.upper()}')
        except Exception as e:
            self.root.title('JP OCR - ENGINE FAILED TO LOAD')
            messagebox.showerror("OCR Load Error", f'Failed to load "{OCR_ENGINE}".\n\nError: {e}')

    def _setup_ui(self):
        self.root.geometry('1600x950')
        # <<< CHANGE 1: Changed 'paned' to 'self.paned' >>>
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(self.paned, padding=0)
        self.canvas = tk.Canvas(left_frame, bg=TEXT_BG, cursor='cross', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.paned.add(left_frame, weight=3)

        right_frame = ttk.Frame(self.paned, padding=10)
        
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 20))

        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        btn_config = {'bg': BTN_COLOR, 'fg': FG_COLOR, 'activebackground': BTN_ACTIVE, 
                      'activeforeground': BG_COLOR, 'font': ('Segoe UI', 10, 'bold'), 
                      'padx': 10, 'pady': 5, 'relief': tk.FLAT, 'highlightthickness': 0}

        tk.Button(btn_frame, text='Open Folder', command=self.open_folder, **btn_config).grid(
            row=0, column=0, columnspan=2, sticky='nsew', pady=1)
        
        tk.Button(btn_frame, text='Prev', command=self.prev_image, **btn_config).grid(
            row=1, column=0, sticky='nsew', pady=1, padx=(0,1))
        tk.Button(btn_frame, text='Next', command=self.next_image, **btn_config).grid(
            row=1, column=1, sticky='nsew', pady=1, padx=(1,0))
        
        tk.Button(btn_frame, text='Zoom In', command=lambda: self.set_zoom(self.zoom * 1.2), **btn_config).grid(
            row=2, column=0, sticky='nsew', pady=1, padx=(0,1))
        tk.Button(btn_frame, text='Zoom Out', command=lambda: self.set_zoom(self.zoom / 1.2), **btn_config).grid(
            row=2, column=1, sticky='nsew', pady=1, padx=(1,0))

        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=15)
        
        tk.Button(right_frame, text='Add Page Marker', command=self.add_page_marker, **btn_config).pack(fill=tk.X, pady=2)
        tk.Button(right_frame, text='Save Output', command=self.save_output, **btn_config).pack(fill=tk.X, pady=(2, 20))

        tk.Label(right_frame, text='Legend Marker', bg=BG_COLOR, fg=FG_COLOR, font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        legend_dd = ttk.Combobox(right_frame, textvariable=self.selected_legend, values=LEGENDS, state='readonly', font=('Segoe UI', 11))
        legend_dd.pack(fill=tk.X, pady=(5, 15))

        text_container = ttk.Frame(right_frame)
        text_container.pack(fill=tk.BOTH, expand=True)
        self.text_output = tk.Text(text_container, font=('Consolas', 13), bg=TEXT_BG, fg=FG_COLOR,
                                   insertbackground=BTN_ACTIVE, wrap=tk.WORD, undo=True, relief=tk.FLAT,
                                   highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.text_output.pack(fill=tk.BOTH, expand=True)

        self.paned.add(right_frame, weight=1)
        
        self.canvas.bind('<ButtonPress-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_move)
        self.canvas.bind('<MouseWheel>', self.on_mouse_scroll)
        self.canvas.bind('<Shift-MouseWheel>', self.on_shift_scroll)
        self.canvas.bind('<Control-MouseWheel>', self.on_ctrl_mouse_wheel)
        self.text_output.bind('<MouseWheel>', lambda e: self.text_output.yview_scroll(int(-1*(e.delta/120)), 'units'))

        # <<< CHANGE 3: Schedule the function to run after the window is drawn >>>
        self.root.after(100, self._set_initial_pane_size)

    # <<< CHANGE 2: Add the new function >>>
    def _set_initial_pane_size(self):
        """Sets the initial 70/30 split for the PanedWindow."""
        try:
            width = self.paned.winfo_width()
            self.paned.sashpos(0, int(width * 0.70))
        except tk.TclError:
            # This can happen if the window is closed before the function runs
            pass

    # --- CORE LOGIC (No changes below this line) ---
    def run_ocr(self, image):
        if not self.ocr_engine:
            messagebox.showerror("OCR Error", "OCR Engine is not loaded. Please restart.")
            return '[OCR NOT LOADED]'
        try:
            if OCR_ENGINE == 'manga-ocr':
                return self.ocr_engine(image)
            elif OCR_ENGINE == 'paddle':
                processed_img = image.convert('L').point(lambda p: 255 if p > 190 else 0)
                img_np = np.array(processed_img)
                result = self.ocr_engine.predict(img_np)
                lines = []
                if result and result[0] is not None:
                    for line_data in result[0]:
                        try:
                            text = line_data[1][0]
                            lines.append(text)
                        except (IndexError, TypeError):
                            pass
                return ''.join(lines)
        except Exception as e:
            print(f"A critical error occurred during OCR: {e}")
            return '[OCR CRITICAL ERROR]'
            
    def add_page_marker(self):
        if self.text_output.get("1.0", tk.END).strip(): self.text_output.insert(tk.END, '\n')
        marker_text = f"page{self.page_counter}\n"
        self.text_output.insert(tk.END, marker_text)
        self.text_output.see(tk.END); self.page_counter += 1

    def on_mouse_up(self, event):
        if not all([self.rect, self.current_image, self.start_x is not None, self.start_y is not None]):
            if self.rect: self.canvas.delete(self.rect)
            self.rect = None
            return

        x0, y0 = self.start_x, self.start_y
        x1, y1 = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        img_x0 = (min(x0, x1) - self.offset[0]) / self.zoom
        img_y0 = (min(y0, y1) - self.offset[1]) / self.zoom
        img_x1 = (max(x0, x1) - self.offset[0]) / self.zoom
        img_y1 = (max(y0, y1) - self.offset[1]) / self.zoom

        if img_x1 - img_x0 < 5 or img_y1 - img_y0 < 5:
            if self.rect: self.canvas.delete(self.rect)
            self.rect = None
            return

        box = (int(img_x0), int(img_y0), int(img_x1), int(img_y1))
        cropped = self.current_image.crop(box)
        text = self.run_ocr(cropped)
        if text:
            legend = self.selected_legend.get()
            if legend == 'none': legend = ''
            line = f"{legend} {text.strip()}\n" if legend else f"{text.strip()}\n"
            self.text_output.insert(tk.END, line)
        if self.rect: self.canvas.delete(self.rect)
        self.rect = None

    def on_mouse_down(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline=BTN_ACTIVE, width=2)

    def on_mouse_drag(self, event):
        if self.rect and self.start_x is not None and self.start_y is not None:
            cur_x, cur_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)
    
    def set_zoom(self, value, center_coords=None):
        old_zoom = self.zoom
        self.zoom = max(0.1, min(8.0, value))
        self.show_image(zoom_ratio=self.zoom/old_zoom, center_coords=center_coords)

    def open_folder(self):
        folder = filedialog.askdirectory()
        if not folder: return
        self.image_paths = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp"))])
        if self.image_paths: self.load_image(0)
        else: messagebox.showinfo("No Images", "No supported image files found.")

    def load_image(self, idx):
        if not self.image_paths: return
        self.img_idx = idx % len(self.image_paths)
        try:
            self.current_image = Image.open(self.image_paths[self.img_idx]).convert('RGB')
            self.zoom = 1.0; self.show_image(is_new_image=True)
            self.root.title(f'JP OCR ({OCR_ENGINE.upper()}) - {os.path.basename(self.image_paths[self.img_idx])}')
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to load image:\n{e}"); self.current_image = None

    def show_image(self, is_new_image=False, zoom_ratio=1.0, center_coords=None):
        if self.current_image is None: return
        w, h = self.current_image.size
        new_w, new_h = int(w * self.zoom), int(h * self.zoom)
        self.tk_img = ImageTk.PhotoImage(self.current_image.resize((new_w, new_h), Image.Resampling.LANCZOS))
        self.canvas.delete('all')
        if is_new_image:
            self.offset = ((self.canvas.winfo_width() - new_w) // 2, (self.canvas.winfo_height() - new_h) // 2)
        elif center_coords:
            img_x, img_y = self.canvas.canvasx(center_coords[0]), self.canvas.canvasy(center_coords[1])
            self.offset = (img_x - (img_x - self.offset[0]) * zoom_ratio, img_y - (img_y - self.offset[1]) * zoom_ratio)
        self.canvas.create_image(self.offset[0], self.offset[1], anchor=tk.NW, image=self.tk_img)
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def prev_image(self):
        if self.image_paths: self.load_image(self.img_idx - 1)
    def next_image(self):
        if self.image_paths: self.load_image(self.img_idx + 1)
    def save_output(self):
        if not self.image_paths: return messagebox.showwarning("Save Error", "No folder open.")
        folder = os.path.dirname(self.image_paths[self.img_idx])
        out_path = filedialog.asksaveasfilename(initialdir=folder, title="Save Text File", defaultextension=".txt", filetypes=[("Text Files", "*.txt")], initialfile="Raw_text.txt")
        if out_path:
            with open(out_path, 'w', encoding='utf-8') as f: f.write(self.text_output.get('1.0', tk.END))
            messagebox.showinfo('Saved', f'Output saved to {out_path}')
    def on_pan_start(self, event): self.canvas.scan_mark(event.x, event.y)
    def on_pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        bbox = self.canvas.bbox('all');
        if bbox: self.offset = (bbox[0], bbox[1])
    def on_mouse_scroll(self, event): self.canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
    def on_shift_scroll(self, event): self.canvas.xview_scroll(int(-1*(event.delta/120)), 'units')
    def on_ctrl_mouse_wheel(self, event):
        self.set_zoom(self.zoom * 1.2 if event.delta > 0 else self.zoom / 1.2, (event.x, event.y))

if __name__ == '__main__':
    root = tk.Tk()
    app = JPOCRApp(root)
    root.mainloop()