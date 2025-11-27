"""
GUI Main Program (Tkinter Version)
FINAL REPAIR V58:
1. STRUCTURAL MIRRORING: Replaced the collapsing "Spacer Frame" in the header with a real Label containing an invisible image.
   This forces the Header's first column to be physically identical to the Song List's first column (Art).
2. PADDING LOCK: Matched the padding (padx=10) on both the Header Art slot and List Art slot.
3. ALIGNMENT: "TITLE" now aligns perfectly with the song names, not the album art.
"""
import tkinter as tk
from tkinter import ttk, filedialog, font
import os
import pygame
import random
from PIL import Image, ImageTk, ImageDraw, ImageOps
import ctypes

# High DPI Fix
try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
except: pass

from music_library import MusicLibrary, _format_duration
from player import (load_songs_from_file, save_songs_to_file)
from audio_player import AudioPlayer

# --- THEME ---
ROOT_BG = "#090E12"
SIDEBAR_BG = "#141E26"
CONTENT_BG = "#141E26"
PLAYER_BG = "#0F171E"
QUEUE_BG = "#141E26"

TEXT_COLOR = "#B0C0D0"
ACCENT_COLOR = "#88CCF1"
WHITE = "#FFFFFF"
HOVER_COLOR = "#1E2A36"
SCROLLBAR_BG = "#1E2A36"
SEPARATOR_COLOR = "#3E3E3E"

# --- CONFIG ---
SCROLLBAR_WIDTH = 12 
COL_ART_WIDTH = 60 
COL_DUR_WIDTH = 80
ALBUM_CARD_WIDTH = 180
ALBUM_CARD_HEIGHT = 340
ALBUM_GRID_PAD = 15

# --- UTILS ---
def create_gradient(width, height, color1, color2):
    r1, g1, b1 = [int(color1[i:i+2], 16) for i in (1, 3, 5)]
    r2, g2, b2 = [int(color2[i:i+2], 16) for i in (1, 3, 5)]
    base = Image.new('RGB', (1, height), color1)
    pixels = base.load()
    for y in range(height):
        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        pixels[0, y] = (r, g, b)
    base = base.resize((width, height), resample=Image.Resampling.NEAREST)
    return ImageTk.PhotoImage(base)

def make_round_image(image_path, size, radius=0, default_color="#22303C"):
    img = None
    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path).resize(size, Image.Resampling.LANCZOS)
        except:
            img = None
            
    if img is None:
        img = Image.new('RGBA', size, default_color)
    
    if radius > 0:
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + size, radius=radius, fill=255)
        img.putalpha(mask)
        
    return ImageTk.PhotoImage(img)

# --- CUSTOM WIDGETS ---

class ModernSlider(tk.Canvas):
    def __init__(self, master, width=300, height=10, command=None, bg_color=PLAYER_BG, **kwargs):
        super().__init__(master, width=width, height=height, bg=bg_color, highlightthickness=0, **kwargs)
        self.command = command
        self.value = 0.0
        self.max_value = 100.0
        self.width = width
        self.height = height
        self.is_hovering = False
        self.is_dragging = False
        cy = height / 2
        self.create_line(0, cy, width, cy, fill="#2C3E50", width=4, capstyle="round", tags="bg")
        self.create_line(0, cy, 0, cy, fill=ACCENT_COLOR, width=4, capstyle="round", tags="fill")
        self.create_oval(0, 0, 0, 0, fill=WHITE, outline="", tags="handle", state="hidden")
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Configure>", self._resize)

    def _resize(self, event):
        self.width = event.width
        cy = self.height / 2
        self.coords("bg", 0, cy, self.width, cy)
        self.update_graphics()

    def _move_to(self, x):
        x = max(0, min(x, self.width))
        ratio = x / self.width
        self.value = ratio * self.max_value
        self.update_graphics()
        if self.command: self.command(self.value)

    def update_graphics(self):
        ratio = self.value / self.max_value if self.max_value > 0 else 0
        x = ratio * self.width
        cy = self.height / 2
        self.coords("fill", 0, cy, x, cy)
        r = 6 
        self.coords("handle", x-r, cy-r, x+r, cy+r)
        if self.is_hovering or self.is_dragging: self.itemconfigure("handle", state="normal")
        else: self.itemconfigure("handle", state="hidden")

    def _on_click(self, event): self.is_dragging = True; self._move_to(event.x)
    def _on_drag(self, event): self.is_dragging = True; self._move_to(event.x)
    def _on_release(self, event): self.is_dragging = False; self.update_graphics()
    def _on_enter(self, event): self.is_hovering = True; self.update_graphics()
    def _on_leave(self, event): self.is_hovering = False; self.update_graphics()
    def set_value(self, val):
        if not self.is_dragging: self.value = val; self.update_graphics()
    def config_range(self, max_val): self.max_value = max_val

class AddSongDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add New Song")
        self.geometry("450x500")
        self.configure(bg=SIDEBAR_BG)
        fields = ["Audio File", "Title", "Artist", "Album", "Track #", "Genre", "Duration (s)", "Album Art"]
        self.entries = {}
        for i, field in enumerate(fields):
            lbl = tk.Label(self, text=field + ":", bg=SIDEBAR_BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold"))
            lbl.grid(row=i, column=0, padx=15, pady=8, sticky="w")
            entry = tk.Entry(self, bg="#22303C", fg=WHITE, insertbackground="white", relief="flat")
            entry.grid(row=i, column=1, padx=15, pady=8, sticky="ew")
            self.entries[field] = entry
            if "File" in field or field == "Album Art":
                btn = tk.Button(self, text="...", command=lambda f=field: self.browse(f), bg="#2C3E50", fg=TEXT_COLOR, relief="flat", width=3)
                btn.grid(row=i, column=2, padx=5)
        self.grid_columnconfigure(1, weight=1)
        tk.Button(self, text="Save Song", command=self.save, bg=ACCENT_COLOR, fg="black", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2").grid(row=len(fields), column=1, pady=20, sticky="ew")

    def browse(self, field):
        f = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav")] if "Audio" in field else [("Images", "*.png *.jpg")])
        if f:
            self.entries[field].delete(0, tk.END); self.entries[field].insert(0, f)
            if "Audio" in field:
                try:
                    snd = pygame.mixer.Sound(f)
                    self.entries["Duration (s)"].delete(0, tk.END); self.entries["Duration (s)"].insert(0, str(int(snd.get_length())))
                    if not self.entries["Title"].get(): self.entries["Title"].insert(0, os.path.splitext(os.path.basename(f))[0])
                except: pass

    def save(self):
        self.master.library.add_song(
            self.entries["Title"].get(), self.entries["Artist"].get(), self.entries["Album"].get(),
            int(self.entries["Track #"].get() or 0), int(self.entries["Duration (s)"].get() or 0),
            self.entries["Genre"].get(), self.entries["Audio File"].get(), self.entries["Album Art"].get()
        )
        save_songs_to_file(self.master.library)
        self.master.show_all_songs_view()
        self.destroy()

class ScrollableFrame(tk.Frame):
    def __init__(self, container, bg_color=CONTENT_BG, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.configure(bg=bg_color)
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = tk.Canvas(container, width=SCROLLBAR_WIDTH, bg=bg_color, highlightthickness=0)
        
        self.scrollbar.create_rectangle(0, 0, SCROLLBAR_WIDTH, 0, fill=SCROLLBAR_BG, outline="", tags="thumb")
        self.scrollbar.bind("<B1-Motion>", self._on_sb_drag)
        self.scrollbar.bind("<Button-1>", self._on_sb_click)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.frame_window, width=e.width))
        self.frame_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.configure(yscrollcommand=self._update_scrollbar)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _update_scrollbar(self, first, last):
        h = self.scrollbar.winfo_height()
        top, bot = float(first) * h, float(last) * h
        if bot - top < 20: bot = top + 20
        self.scrollbar.coords("thumb", 2, top, SCROLLBAR_WIDTH-2, bot)

    def _on_sb_drag(self, event):
        h = self.scrollbar.winfo_height()
        self.canvas.yview_moveto(event.y / h)
    def _on_sb_click(self, event): self._on_sb_drag(event)
    
    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        if self.scrollable_frame.winfo_reqheight() <= self.canvas.winfo_height(): self.canvas.unbind_all("<MouseWheel>")
        else: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

class MusicifyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Musicify")
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = int(screen_w * 0.8)
        win_h = int(screen_h * 0.8)
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        
        self.configure(bg=ROOT_BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.library = MusicLibrary(); load_songs_from_file(self.library)
        self.player = AudioPlayer()
        self.player.on_song_changed = self.update_now_playing_ui
        self.player.on_queue_changed = self.update_queue_ui
        self.player.on_playback_state_changed = self.update_play_icon
        
        self.current_view_songs = []
        self.image_refs = {} 
        self.grad_img = None 
        self.view_mode = "list"
        self.album_cards = []
        self.queue_labels = []
        self.resize_timer = None
        self.last_cols = 0
        self.is_album_view = False 
        
        self.font_title = font.Font(family="Segoe UI", size=9, weight="bold")
        self.font_artist = font.Font(family="Segoe UI", size=8)

        self.setup_ui()
        self.show_all_songs_view()
        
        self.after(100, self.force_layout)
        self.after(100, self.update_progress)

    def force_layout(self):
        self.update_idletasks()
        w = self.winfo_width()
        try:
            self.main_paned.sash_place(0, 260, 0)
            self.main_paned.sash_place(1, w - 240, 0)
        except: pass

    def load_icon(self, path, size, rounded=False):
        if rounded: return make_round_image(path, size, radius=5)
        return make_round_image(path, size, radius=0)

    def _configure_grid_columns(self, frame, is_header=False):
        # 0: Art (Fixed) | 1: Title (Stretch) | 2: Album (Stretch) | 3: Time (Fixed) | 4: Spacer (Fixed)
        frame.grid_columnconfigure(0, minsize=COL_ART_WIDTH, weight=0)   
        frame.grid_columnconfigure(1, weight=5)     
        frame.grid_columnconfigure(2, weight=3)  
        frame.grid_columnconfigure(3, minsize=COL_DUR_WIDTH, weight=0)
        
        if is_header:
             frame.grid_columnconfigure(4, minsize=SCROLLBAR_WIDTH, weight=0)

    def setup_ui(self):
        self.setup_bottom_player()

        self.main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=SEPARATOR_COLOR, sashwidth=1, showhandle=False, sashrelief=tk.FLAT)
        self.main_paned.pack(side="top", fill="both", expand=True)
        
        # Sidebar
        self.sidebar = tk.Frame(self.main_paned, bg=SIDEBAR_BG)
        self.main_paned.add(self.sidebar, minsize=150, width=260, stretch="never")
        
        tk.Label(self.sidebar, text="Musicify", bg=SIDEBAR_BG, fg=WHITE, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=35, pady=20)
        self.btn_all = tk.Button(self.sidebar, text="All Songs", command=self.show_all_songs_view, bg=SIDEBAR_BG, fg=TEXT_COLOR, font=("Segoe UI", 11, "bold"), bd=0, activebackground=SIDEBAR_BG, activeforeground=WHITE, anchor="w", padx=35)
        self.btn_all.pack(fill="x", pady=5)
        self.btn_alb = tk.Button(self.sidebar, text="Albums", command=self.show_albums_view, bg=SIDEBAR_BG, fg=TEXT_COLOR, font=("Segoe UI", 11, "bold"), bd=0, activebackground=SIDEBAR_BG, activeforeground=WHITE, anchor="w", padx=35)
        self.btn_alb.pack(fill="x", pady=5)
        tk.Frame(self.sidebar, bg="#282828", height=1).pack(fill="x", padx=35, pady=15)
        tk.Button(self.sidebar, text="+ Add New Song", command=lambda: AddSongDialog(self), bg=SIDEBAR_BG, fg=ACCENT_COLOR, font=("Segoe UI", 11, "bold"), bd=0, activebackground=SIDEBAR_BG, activeforeground=WHITE, anchor="w", padx=35).pack(fill="x")

        # Content
        self.content = tk.Frame(self.main_paned, bg=CONTENT_BG)
        self.main_paned.add(self.content, stretch="always")
        
        self.header_frame = tk.Frame(self.content, bg=CONTENT_BG, height=200)
        self.header_frame.pack(fill="x"); self.header_frame.pack_propagate(False)
        self.header_canvas = tk.Canvas(self.header_frame, bg=CONTENT_BG, highlightthickness=0)
        self.header_canvas.place(relwidth=1, relheight=1)
        self.header_frame.bind("<Configure>", self.update_gradient)
        
        self.title_text_id = self.header_canvas.create_text(30, 80, text="All Songs", font=("Segoe UI", 48, "bold"), fill=WHITE, anchor="w")
        self.icon_play_big = self.load_icon("assets/play.png", (56, 56), rounded=True) 
        self.btn_play_id = self.header_canvas.create_image(30, 140, image=self.icon_play_big, anchor="nw", tags="controls")
        self.header_canvas.tag_bind(self.btn_play_id, "<Button-1>", lambda e: self.play_current_view())
        self.btn_shuf_id = self.header_canvas.create_text(110, 168, text="SHUFFLE", fill=TEXT_COLOR, font=("Segoe UI", 10, "bold"), anchor="w", tags="controls")
        self.header_canvas.tag_bind(self.btn_shuf_id, "<Button-1>", lambda e: self.shuffle_current_view())
        
        # --- INIT LIST FIRST ---
        self.list_container = ScrollableFrame(self.content, bg_color=CONTENT_BG)
        self.list_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        self.list_container.canvas.bind("<Configure>", self.on_content_resize)
        
        # --- THEN HEADER ---
        self.sticky_header = tk.Frame(self.content, bg=CONTENT_BG)
        self.sticky_header.pack(fill="x", padx=30, pady=(0, 0), before=self.list_container) 
        self._configure_grid_columns(self.sticky_header, is_header=True)

        # Queue
        self.queue_panel = tk.Frame(self.main_paned, bg=QUEUE_BG)
        self.main_paned.add(self.queue_panel, minsize=150, width=240, stretch="never")
        tk.Label(self.queue_panel, text="Up Next", bg=QUEUE_BG, fg="#6B7D8C", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=20)
        self.queue_container = ScrollableFrame(self.queue_panel, bg_color=QUEUE_BG)
        self.queue_container.pack(fill="both", expand=True, padx=0)
        tk.Button(self.queue_panel, text="Clear Queue", command=self.player.clear_queue, bg=QUEUE_BG, fg=TEXT_COLOR, bd=0, cursor="hand2", font=("Segoe UI", 9)).pack(pady=15)
        self.queue_panel.bind("<Configure>", self.on_queue_resize)

    def setup_bottom_player(self):
        bottom = tk.Frame(self, bg=PLAYER_BG, height=90, bd=0, relief="flat")
        bottom.pack(side="bottom", fill="x"); bottom.pack_propagate(False)
        tk.Frame(bottom, bg=SEPARATOR_COLOR, height=1).place(x=0, y=0, relwidth=1)
        bottom.columnconfigure(0, weight=1, uniform="sides"); bottom.columnconfigure(1, weight=2); bottom.columnconfigure(2, weight=1, uniform="sides"); bottom.rowconfigure(0, weight=1)
        info = tk.Frame(bottom, bg=PLAYER_BG); info.grid(row=0, column=0, sticky="w", padx=20)
        art_f = tk.Frame(info, width=56, height=56, bg="#222"); art_f.pack(side="left"); art_f.pack_propagate(False)
        self.lbl_mini_art = tk.Label(art_f, bg="#222"); self.lbl_mini_art.pack(expand=True, fill="both")
        txt_f = tk.Frame(info, bg=PLAYER_BG); txt_f.pack(side="left", padx=15)
        self.lbl_mini_title = tk.Label(txt_f, text="No song selected", bg=PLAYER_BG, fg=WHITE, font=("Segoe UI", 10)); self.lbl_mini_title.pack(anchor="w")
        self.lbl_mini_artist = tk.Label(txt_f, text="", bg=PLAYER_BG, fg=ACCENT_COLOR, font=("Segoe UI", 9)); self.lbl_mini_artist.pack(anchor="w")
        center = tk.Frame(bottom, bg=PLAYER_BG); center.grid(row=0, column=1)
        self.ico_prev = self.load_icon("assets/prev.png", (16, 16)); self.ico_play = self.load_icon("assets/play.png", (32, 32))
        self.ico_pause = self.load_icon("assets/pause.png", (32, 32)); self.ico_skip = self.load_icon("assets/skip.png", (16, 16))
        btns = tk.Frame(center, bg=PLAYER_BG); btns.pack(pady=(10, 5))
        tk.Button(btns, image=self.ico_prev, bg=PLAYER_BG, activebackground=PLAYER_BG, bd=0, cursor="hand2", command=self.player.play_previous_song).pack(side="left", padx=15)
        self.btn_play = tk.Button(btns, image=self.ico_play, bg=PLAYER_BG, activebackground=PLAYER_BG, bd=0, cursor="hand2", command=self.player.toggle_playback); self.btn_play.pack(side="left", padx=15)
        tk.Button(btns, image=self.ico_skip, bg=PLAYER_BG, activebackground=PLAYER_BG, bd=0, cursor="hand2", command=self.player.skip_to_next).pack(side="left", padx=15)
        slider_f = tk.Frame(center, bg=PLAYER_BG); slider_f.pack(fill="x")
        self.lbl_cur = tk.Label(slider_f, text="-:--", bg=PLAYER_BG, fg=TEXT_COLOR, font=("Segoe UI", 8)); self.lbl_cur.pack(side="left", padx=5)
        self.slider = ModernSlider(slider_f, width=400, height=12, bg_color=PLAYER_BG, command=lambda v: self.player.seek(float(v))); self.slider.pack(side="left", padx=5)
        self.lbl_tot = tk.Label(slider_f, text="-:--", bg=PLAYER_BG, fg=TEXT_COLOR, font=("Segoe UI", 8)); self.lbl_tot.pack(side="left", padx=5)
        right = tk.Frame(bottom, bg=PLAYER_BG); right.grid(row=0, column=2, sticky="e", padx=20)

    def update_gradient(self, event):
        w, h = event.width, event.height
        if w < 10: return
        self.grad_img = create_gradient(w, h, ROOT_BG, CONTENT_BG)
        self.header_canvas.create_image(0, 0, anchor="nw", image=self.grad_img)
        self.header_canvas.tag_raise(self.title_text_id)
        self.header_canvas.tag_raise("controls")

    def set_sidebar_active(self, mode):
        self.btn_all.config(fg=TEXT_COLOR)
        self.btn_alb.config(fg=TEXT_COLOR)
        if mode == "all": self.btn_all.config(fg=WHITE)
        else: self.btn_alb.config(fg=WHITE)

    def play_song_from_view(self, index):
        if 0 <= index < len(self.current_view_songs):
            song = self.current_view_songs[index]
            self.player.play_now(song)
            self.player.clear_queue()
            if self.is_album_view:
                remaining = self.current_view_songs[index+1:]
                for s in remaining: self.player.add_to_queue(s)

    def show_context_menu(self, event, song):
        menu = tk.Menu(self, tearoff=0, bg=PLAYER_BG, fg=WHITE, activebackground=HOVER_COLOR)
        menu.add_command(label="Add to Queue", command=lambda: self.player.add_to_queue(song))
        menu.post(event.x_root, event.y_root)

    def refresh_list(self, songs, is_album=False):
        self.view_mode = "list"
        self.album_cards = []
        self.is_album_view = is_album 
        self.current_view_songs = songs
        
        # --- UPDATE STICKY HEADER ---
        for w in self.sticky_header.winfo_children(): w.destroy()
        
        if is_album or self.view_mode == "list":
            self.sticky_header.pack(fill="x", padx=30, pady=(0, 0), before=self.list_container) 
            h_font = ("Segoe UI", 9, "bold")
            
            # FIX: Phantom Label to mimic Art Column width & padding
            # We use an invisible 48x48 image (same as song list)
            # Padding is (10,0) because list art uses padx=10
            self.header_ph = make_round_image(None, (48,48), default_color=CONTENT_BG) # Invisible
            lbl_art = tk.Label(self.sticky_header, image=self.header_ph, bg=CONTENT_BG, bd=0)
            lbl_art.grid(row=0, column=0, sticky="w", pady=10, padx=(10,0))
            
            tk.Label(self.sticky_header, text="TITLE", bg=CONTENT_BG, fg=TEXT_COLOR, font=h_font).grid(row=0, column=1, sticky="w", pady=10, padx=(10, 0))
            tk.Label(self.sticky_header, text="ALBUM", bg=CONTENT_BG, fg=TEXT_COLOR, font=h_font).grid(row=0, column=2, sticky="w", pady=10)
            tk.Label(self.sticky_header, text="🕒", bg=CONTENT_BG, fg=TEXT_COLOR, font=h_font).grid(row=0, column=3, sticky="e", pady=10, padx=(0,10))
            tk.Frame(self.sticky_header, width=SCROLLBAR_WIDTH, bg=CONTENT_BG).grid(row=0, column=4, sticky="e")
            tk.Frame(self.sticky_header, bg="#1E2A36", height=1).grid(row=1, column=0, columnspan=5, sticky="ew", pady=(0, 0))
        else:
            self.sticky_header.pack_forget()

        frame = self.list_container.scrollable_frame
        for w in frame.winfo_children(): w.destroy()
        
        if is_album:
            for c in range(5): frame.grid_columnconfigure(c, weight=0, minsize=0)
        else:
            self._configure_grid_columns(frame)

        start_row = 0

        for i, song in enumerate(songs, start=start_row):
            r = i
            list_idx = i - start_row
            cmd = lambda e, idx=list_idx: self.play_song_from_view(idx)
            r_click = lambda e, s=song: self.show_context_menu(e, s)
            def on_ent(e, r=r):
                for w in frame.grid_slaves(row=r): w.config(bg=HOVER_COLOR)
            def on_lve(e, r=r):
                for w in frame.grid_slaves(row=r): w.config(bg=CONTENT_BG)

            if is_album:
                l = tk.Label(frame, text=str(song.track_number), bg=CONTENT_BG, fg=TEXT_COLOR)
                l.grid(row=r, column=0, sticky="w", pady=8, padx=(15,0))
                l.bind("<Enter>", on_ent); l.bind("<Leave>", on_lve); l.bind("<Button-3>", r_click)
            else:
                # Art Column: 48x48, padx=10 to match header
                icon = self.load_icon(song.image_path, (48, 48), rounded=True)
                if icon:
                    self.image_refs[f"s{i}"] = icon
                    lbl = tk.Label(frame, image=icon, bg=CONTENT_BG, bd=0)
                    lbl.grid(row=r, column=0, sticky="w", pady=5, padx=(10,0))
                    lbl.bind("<Button-1>", cmd); lbl.bind("<Enter>", on_ent); lbl.bind("<Leave>", on_lve); lbl.bind("<Button-3>", r_click)
                else:
                    # Ensure placeholder maintains grid structure
                    ph = make_round_image(None, (48,48))
                    self.image_refs[f"s{i}_ph"] = ph
                    lbl = tk.Label(frame, image=ph, bg=CONTENT_BG, bd=0)
                    lbl.grid(row=r, column=0, sticky="w", pady=5, padx=(10,0))
                    lbl.bind("<Button-1>", cmd); lbl.bind("<Enter>", on_ent); lbl.bind("<Leave>", on_lve); lbl.bind("<Button-3>", r_click)

            meta = tk.Frame(frame, bg=CONTENT_BG)
            # Title Column: padx=10 to match header
            meta.grid(row=r, column=1, sticky="we", padx=(10, 5))
            t = tk.Label(meta, text=song.title, bg=CONTENT_BG, fg=WHITE, font=("Segoe UI", 10), anchor="w")
            t.pack(fill="x")
            a = tk.Label(meta, text=song.artist, bg=CONTENT_BG, fg=TEXT_COLOR, font=("Segoe UI", 9), anchor="w")
            a.pack(fill="x")
            for w in [meta, t, a]: w.bind("<Button-1>", cmd); w.bind("<Enter>", on_ent); w.bind("<Leave>", on_lve); w.bind("<Button-3>", r_click)

            l2 = tk.Label(frame, text=song.album, bg=CONTENT_BG, fg=TEXT_COLOR, anchor="w")
            l2.grid(row=r, column=2, sticky="we")
            l2.bind("<Enter>", on_ent); l2.bind("<Leave>", on_lve); l2.bind("<Button-3>", r_click)

            l3 = tk.Label(frame, text=_format_duration(song.duration), bg=CONTENT_BG, fg=TEXT_COLOR, anchor="e")
            l3.grid(row=r, column=3, sticky="e", padx=(0,10))
            l3.bind("<Enter>", on_ent); l3.bind("<Leave>", on_lve); l3.bind("<Button-3>", r_click)

    def show_all_songs_view(self):
        self.header_canvas.itemconfig(self.title_text_id, text="All Songs")
        self.header_canvas.itemconfigure("controls", state="hidden")
        self.set_sidebar_active("all")
        self.refresh_list(self.library.get_sorted_song_list(), is_album=False)

    def show_albums_view(self):
        self.header_canvas.itemconfig(self.title_text_id, text="Albums")
        self.header_canvas.itemconfigure("controls", state="hidden")
        self.set_sidebar_active("albums")
        self.sticky_header.pack_forget()
        
        frame = self.list_container.scrollable_frame
        for w in frame.winfo_children(): w.destroy()
        self.view_mode = "album_grid"
        self.album_cards = []
        self.is_album_view = False 
        self.last_cols = 0 
        albums = self.library.get_songs_by_album()
        for i, album in enumerate(albums):
            card = tk.Frame(frame, bg=SIDEBAR_BG, width=ALBUM_CARD_WIDTH, height=ALBUM_CARD_HEIGHT)
            card.pack_propagate(False)
            def on_c_ent(e, c=card): c.config(bg=HOVER_COLOR)
            def on_c_lve(e, c=card): c.config(bg=SIDEBAR_BG)
            card.bind("<Enter>", on_c_ent); card.bind("<Leave>", on_c_lve)
            songs = albums[album]
            if songs and songs[0].image_path:
                icon = self.load_icon(songs[0].image_path, (160, 160), rounded=True)
                if icon:
                    self.image_refs[f"alb{i}"] = icon
                    btn = tk.Button(card, image=icon, bg=SIDEBAR_BG, bd=0, activebackground=SIDEBAR_BG, command=lambda a=album: self.open_album(a))
                    btn.pack(pady=15)
                    btn.bind("<Enter>", lambda e, c=card: c.config(bg=HOVER_COLOR))
                    btn.bind("<Leave>", lambda e, c=card: c.config(bg=SIDEBAR_BG))
            lbl = tk.Label(card, text=album, bg=SIDEBAR_BG, fg=WHITE, font=("Segoe UI", 10, "bold"), wraplength=160, justify="left")
            lbl.pack(anchor="w", padx=10)
            lbl.bind("<Enter>", lambda e, c=card: c.config(bg=HOVER_COLOR))
            artist_name = songs[0].artist if songs else "Unknown"
            lbl2 = tk.Label(card, text=artist_name, bg=SIDEBAR_BG, fg=TEXT_COLOR, font=("Segoe UI", 9), wraplength=160, justify="left")
            lbl2.pack(anchor="w", padx=10)
            lbl2.bind("<Enter>", lambda e, c=card: c.config(bg=HOVER_COLOR))
            self.album_cards.append(card)
        self.on_content_resize(None)

    def on_content_resize(self, event):
        if self.view_mode != "album_grid": return
        width = self.list_container.canvas.winfo_width()
        if width < 100: return
        slot_width = ALBUM_CARD_WIDTH + (ALBUM_GRID_PAD * 2)
        cols = max(1, width // slot_width)
        if cols == self.last_cols: return
        self.last_cols = cols
        for i, card in enumerate(self.album_cards):
            row = i // cols
            col = i % cols
            card.grid(row=row, column=col, padx=ALBUM_GRID_PAD, pady=ALBUM_GRID_PAD)

    def on_queue_resize(self, event):
        if self.resize_timer: self.after_cancel(self.resize_timer)
        self.resize_timer = self.after(50, lambda: self._update_queue_text(event.width))

    def _update_queue_text(self, width):
        char_limit = max(10, (width - 60) // 8)
        for lbl, full_text in self.queue_labels:
            f = self.font_title if lbl.cget("font") == "Segoe UI 9 bold" else self.font_artist
            if f.measure(full_text) <= (width - 60):
                lbl.config(text=full_text)
            else:
                t = full_text
                while f.measure(t + "...") > (width - 60) and len(t) > 0:
                    t = t[:-1]
                lbl.config(text=t + "...")

    def update_now_playing_ui(self, song):
        if song:
            self.lbl_mini_title.config(text=song.title)
            self.lbl_mini_artist.config(text=song.artist)
            self.lbl_tot.config(text=_format_duration(song.duration))
            self.slider.config_range(song.duration)
            self.btn_play.config(image=self.ico_pause)
            if song.image_path:
                icon = self.load_icon(song.image_path, (56, 56), rounded=False)
                if icon: self.image_refs["mini"] = icon; self.lbl_mini_art.config(image=icon)
        else:
            self.btn_play.config(image=self.ico_play)

    def update_queue_ui(self, queue):
        frame = self.queue_container.scrollable_frame
        for w in frame.winfo_children(): w.destroy()
        self.queue_labels = []
        
        for i, song in enumerate(queue):
            row = tk.Frame(frame, bg=QUEUE_BG, height=60)
            row.pack(fill="x", pady=0)
            row.pack_propagate(False)
            
            def on_click(e, idx=i): self.player.skip_to_index(idx)
            def on_ent(e, r=row): r.config(bg=HOVER_COLOR)
            def on_lve(e, r=row): r.config(bg=QUEUE_BG)

            row.bind("<Double-Button-1>", on_click)
            row.bind("<Enter>", on_ent)
            row.bind("<Leave>", on_lve)

            lbl_num = tk.Label(row, text=str(i+1), bg=QUEUE_BG, fg=TEXT_COLOR, width=4)
            lbl_num.pack(side="left")
            
            info = tk.Frame(row, bg=QUEUE_BG)
            info.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            lbl_title = tk.Label(info, text=song.title, bg=QUEUE_BG, fg=WHITE, font=("Segoe UI", 9, "bold"), anchor="w")
            lbl_title.pack(fill="x")
            self.queue_labels.append((lbl_title, song.title))
            
            lbl_artist = tk.Label(info, text=song.artist, bg=QUEUE_BG, fg=TEXT_COLOR, font=("Segoe UI", 8), anchor="w")
            lbl_artist.pack(fill="x")
            self.queue_labels.append((lbl_artist, song.artist))

            for w in (lbl_num, info, lbl_title, lbl_artist):
                w.bind("<Double-Button-1>", on_click)
                w.bind("<Enter>", on_ent)
                w.bind("<Leave>", on_lve)
        
        self._update_queue_text(self.queue_panel.winfo_width())

    def update_play_icon(self, is_playing):
        self.btn_play.config(image=self.ico_pause if is_playing else self.ico_play)

    def update_progress(self):
        if self.player.is_playing:
            cur = self.player.get_current_position()
            self.slider.set_value(cur)
            self.lbl_cur.config(text=_format_duration(cur))
        self.after(500, self.update_progress)

    def on_seek(self, val):
        self.player.seek(float(val))

    def on_close(self):
        print("Auto-saving on exit...")
        print(save_songs_to_file(self.library))
        self.destroy()

if __name__ == "__main__":
    app = MusicifyApp()
    app.mainloop()