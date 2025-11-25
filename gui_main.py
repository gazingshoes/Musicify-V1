"""
GUI Main Program (Tkinter Version)
FINAL REPAIR V15:
1. SEPARATORS RESTORED: Sidebar, Content, and Queue are now separate panels with gaps.
2. CANVAS HEADER BUTTONS: Play/Shuffle are transparent (drawn on canvas).
3. BLUE THEME: Kept the blue color palette while using the panel layout.
"""
import tkinter as tk
from tkinter import ttk, filedialog
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

# --- GENTLE BLUE THEME COLORS ---
ROOT_BG = "#090E12"         # Dark gap color
SIDEBAR_COLOR = "#141E26"   # Panel Color
BG_COLOR = "#141E26"        # Main Content Color
PLAYER_BG = "#0F171E"       # Bottom Player
TEXT_COLOR = "#B0C0D0"
ACCENT_COLOR = "#88CCF1"
WHITE = "#FFFFFF"
HOVER_COLOR = "#1E2A36"
SCROLLBAR_BG = "#1E2A36"
QUEUE_BG_1 = "#141E26"
QUEUE_BG_2 = "#18222D" 
SEPARATOR_COLOR = "#3E3E3E"

# --- CONFIG ---
COL_ART_WIDTH = 60
COL_ALBUM_WIDTH = 200
COL_DUR_WIDTH = 80

# --- UTILS ---
def create_gradient(width, height, color1, color2):
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    top.paste(base, (0, 0), mask)
    return ImageTk.PhotoImage(top)

def make_round_image(image_path, size, radius=10):
    try:
        if not os.path.exists(image_path): return None
        img = Image.open(image_path).resize(size, Image.Resampling.LANCZOS)
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + size, radius=radius, fill=255)
        output = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        return ImageTk.PhotoImage(output)
    except: return None

# --- CUSTOM WIDGETS ---

class ModernSlider(tk.Canvas):
    def __init__(self, master, width=300, height=50, command=None, **kwargs):
        super().__init__(master, width=width, height=height, bg=PLAYER_BG, highlightthickness=0, **kwargs)
        self.command = command
        self.value = 0.0
        self.max_value = 100.0
        self.width = width
        self.height = height
        self.padding = 20 
        self.is_hovering = False
        self.is_dragging = False
        
        cy = height / 2
        self.create_line(self.padding, cy, width-self.padding, cy, fill="#2C3E50", width=4, capstyle="round", tags="bg")
        self.create_line(self.padding, cy, self.padding, cy, fill=ACCENT_COLOR, width=4, capstyle="round", tags="fill")
        self.create_oval(0, 0, 0, 0, fill=WHITE, outline=PLAYER_BG, tags="handle", state="hidden")
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Configure>", self._resize)

    def _resize(self, event):
        self.width = event.width
        cy = self.height / 2
        self.coords("bg", self.padding, cy, self.width-self.padding, cy)
        self.update_graphics()

    def _move_to(self, x):
        x = max(self.padding, min(x, self.width - self.padding))
        ratio = (x - self.padding) / (self.width - (2 * self.padding))
        self.value = ratio * self.max_value
        self.update_graphics()
        if self.command: self.command(self.value)

    def update_graphics(self):
        usable = self.width - (2 * self.padding)
        ratio = self.value / self.max_value if self.max_value > 0 else 0
        x = self.padding + (ratio * usable)
        cy = self.height / 2
        self.coords("fill", self.padding, cy, x, cy)
        r = 7 
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

class ModernScrollbar(tk.Canvas):
    def __init__(self, master, command=None, bg_color=BG_COLOR, **kwargs):
        super().__init__(master, width=8, bg=bg_color, highlightthickness=0, **kwargs)
        self.command = command
        self.create_rectangle(0, 0, 8, 0, fill="#38444D", outline="", tags="thumb")
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.y_top = 0.0; self.y_bottom = 1.0

    def set(self, first, last):
        self.y_top = float(first); self.y_bottom = float(last); self.update_graphics()

    def update_graphics(self):
        h = self.winfo_height(); top = self.y_top * h; bot = self.y_bottom * h
        if bot - top < 20: bot = top + 20
        self.coords("thumb", 0, top, 8, bot)

    def _on_click(self, event):
        h = self.winfo_height(); y = event.y / h
        if self.command: self.command("moveto", y)
    def _on_drag(self, event): self._on_click(event)

class AddSongDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add New Song")
        self.geometry("450x500")
        self.configure(bg=SIDEBAR_COLOR)
        
        fields = ["Audio File", "Title", "Artist", "Album", "Track #", "Genre", "Duration (s)", "Album Art"]
        self.entries = {}
        for i, field in enumerate(fields):
            lbl = tk.Label(self, text=field + ":", bg=SIDEBAR_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold"))
            lbl.grid(row=i, column=0, padx=15, pady=8, sticky="w")
            entry = tk.Entry(self, bg="#22303C", fg=WHITE, insertbackground="white", relief="flat")
            entry.grid(row=i, column=1, padx=15, pady=8, sticky="ew")
            self.entries[field] = entry
            if "File" in field or "Art" in field:
                btn = tk.Button(self, text="...", command=lambda f=field: self.browse(f), bg="#2C3E50", fg=TEXT_COLOR, relief="flat", width=3)
                btn.grid(row=i, column=2, padx=5)
        self.grid_columnconfigure(1, weight=1)
        tk.Button(self, text="Save Song", command=self.save, bg=ACCENT_COLOR, fg="black", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2").grid(row=len(fields), column=1, pady=20, sticky="ew")

    def browse(self, field):
        ftypes = [("Audio", "*.mp3 *.wav")] if "Audio" in field else [("Images", "*.png *.jpg")]
        f = filedialog.askopenfilename(filetypes=ftypes)
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
    def __init__(self, container, bg_color=BG_COLOR, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.configure(bg=bg_color)
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = ModernScrollbar(container, command=self.canvas.yview, bg_color=bg_color)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.frame_window, width=e.width))
        self.frame_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Scrollbar packed in parent, canvas packed here
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        if self.scrollable_frame.winfo_reqheight() <= self.canvas.winfo_height():
            self.canvas.unbind_all("<MouseWheel>")
        else:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

class MusicifyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Musicify")
        self.geometry("1200x800")
        # ROOT BACKGROUND IS THE GAP COLOR
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

        self.setup_ui()
        self.show_all_songs_view()
        self.after(100, self.update_progress)

    def load_icon(self, path, size, rounded=False):
        if rounded: return make_round_image(path, size, radius=5)
        try:
            if not os.path.exists(path): return None
            img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except: return None

    def _configure_grid_columns(self, frame):
        frame.grid_columnconfigure(0, minsize=60)   
        frame.grid_columnconfigure(1, weight=1)     
        frame.grid_columnconfigure(2, minsize=200)  
        frame.grid_columnconfigure(3, minsize=80)   

    def setup_ui(self):
        # 1. BOTTOM PLAYER (Reserves space at bottom)
        self.setup_bottom_player()

        # 2. MAIN CONTAINER (Fills remaining space)
        # This frame uses ROOT_BG to create the "gaps" between the panels
        main = tk.Frame(self, bg=ROOT_BG)
        main.pack(side="top", fill="both", expand=True)
        
        # --- 3. PANELS WITH PADDING (Gaps) ---
        
        # Left Sidebar
        sidebar = tk.Frame(main, bg=SIDEBAR_COLOR, width=220)
        sidebar.pack(side="left", fill="y", padx=(0, 8), pady=8); sidebar.pack_propagate(False)
        
        self.btn_all = tk.Button(sidebar, text="All Songs", command=self.show_all_songs_view, bg=SIDEBAR_COLOR, fg=WHITE, font=("Segoe UI", 12, "bold"), bd=0, activebackground=HOVER_COLOR, activeforeground=WHITE, anchor="w", padx=20)
        self.btn_all.pack(fill="x", pady=(30, 5))
        self.btn_alb = tk.Button(sidebar, text="Albums", command=self.show_albums_view, bg=SIDEBAR_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 12, "bold"), bd=0, activebackground=HOVER_COLOR, activeforeground=WHITE, anchor="w", padx=20)
        self.btn_alb.pack(fill="x", pady=5)
        tk.Button(sidebar, text="+ Add New Song", command=lambda: AddSongDialog(self), bg=SIDEBAR_COLOR, fg=ACCENT_COLOR, font=("Segoe UI", 12, "bold"), bd=0, activebackground=HOVER_COLOR, activeforeground=WHITE, anchor="w", padx=20).pack(side="bottom", fill="x", pady=30)

        # Right Sidebar
        rightbar = tk.Frame(main, bg=SIDEBAR_COLOR, width=220)
        rightbar.pack(side="right", fill="y", padx=(8, 0), pady=8); rightbar.pack_propagate(False)
        tk.Label(rightbar, text="UP NEXT", bg=SIDEBAR_COLOR, fg="#6B7D8C", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=30)
        self.queue_container = ScrollableFrame(rightbar, bg_color=SIDEBAR_COLOR)
        self.queue_container.pack(fill="both", expand=True, padx=5)
        tk.Button(rightbar, text="Clear Queue", command=self.player.clear_queue, bg=SIDEBAR_COLOR, fg=TEXT_COLOR, bd=0, cursor="hand2").pack(pady=20)

        # Center Content
        self.content = tk.Frame(main, bg=BG_COLOR)
        self.content.pack(side="left", fill="both", expand=True, pady=8)
        
        self.header_frame = tk.Frame(self.content, bg=BG_COLOR, height=220)
        self.header_frame.pack(fill="x", padx=0, pady=0); self.header_frame.pack_propagate(False)
        self.header_canvas = tk.Canvas(self.header_frame, bg=BG_COLOR, highlightthickness=0)
        self.header_canvas.place(relwidth=1, relheight=1)
        self.header_frame.bind("<Configure>", self.update_gradient)
        self.title_text_id = self.header_canvas.create_text(40, 60, text="All Songs", font=("Segoe UI", 40, "bold"), fill=WHITE, anchor="w")
        
        # CANVAS CONTROLS (True Transparency)
        self.icon_play_big = self.load_icon("assets/play.png", (60, 60))
        self.btn_play_id = self.header_canvas.create_image(40, 120, image=self.icon_play_big, anchor="nw", state="hidden", tags="controls")
        self.header_canvas.tag_bind(self.btn_play_id, "<Button-1>", lambda e: self.play_current_view())
        self.header_canvas.tag_bind(self.btn_play_id, "<Enter>", lambda e: self.header_canvas.config(cursor="hand2"))
        self.header_canvas.tag_bind(self.btn_play_id, "<Leave>", lambda e: self.header_canvas.config(cursor=""))
        
        self.btn_shuf_id = self.header_canvas.create_text(120, 150, text="Shuffle", fill="#B0C0D0", font=("Segoe UI", 12, "bold"), anchor="w", state="hidden", tags="controls")
        self.header_canvas.tag_bind(self.btn_shuf_id, "<Button-1>", lambda e: self.shuffle_current_view())
        self.header_canvas.tag_bind(self.btn_shuf_id, "<Enter>", lambda e: self.header_canvas.itemconfig(self.btn_shuf_id, fill=WHITE))
        self.header_canvas.tag_bind(self.btn_shuf_id, "<Leave>", lambda e: self.header_canvas.itemconfig(self.btn_shuf_id, fill="#B0C0D0"))

        self.list_container = ScrollableFrame(self.content, bg_color=BG_COLOR)
        self.list_container.pack(fill="both", expand=True, padx=20)

    def setup_bottom_player(self):
        bottom = tk.Frame(self, bg=PLAYER_BG, height=100, bd=1, relief="solid")
        bottom.pack(side="bottom", fill="x"); bottom.pack_propagate(False)
        bottom.columnconfigure(0, weight=1, uniform="grp")
        bottom.columnconfigure(1, weight=2, uniform="grp")
        bottom.columnconfigure(2, weight=1, uniform="grp")
        bottom.rowconfigure(0, weight=1)

        info = tk.Frame(bottom, bg=PLAYER_BG); info.grid(row=0, column=0, sticky="w", padx=20)
        art_f = tk.Frame(info, width=50, height=50, bg="#222"); art_f.pack(side="left"); art_f.pack_propagate(False)
        self.lbl_mini_art = tk.Label(art_f, bg="#222"); self.lbl_mini_art.pack(expand=True, fill="both")
        txt_f = tk.Frame(info, bg=PLAYER_BG); txt_f.pack(side="left", padx=10)
        self.lbl_mini_title = tk.Label(txt_f, text="Select a song", bg=PLAYER_BG, fg=WHITE, font=("Segoe UI", 10, "bold")); self.lbl_mini_title.pack(anchor="w")
        self.lbl_mini_artist = tk.Label(txt_f, text="", bg=PLAYER_BG, fg=ACCENT_COLOR, font=("Segoe UI", 9)); self.lbl_mini_artist.pack(anchor="w")

        center = tk.Frame(bottom, bg=PLAYER_BG); center.grid(row=0, column=1)
        self.ico_prev = self.load_icon("assets/prev.png", (24, 24)); self.ico_play = self.load_icon("assets/play.png", (42, 42))
        self.ico_pause = self.load_icon("assets/pause.png", (42, 42)); self.ico_skip = self.load_icon("assets/skip.png", (24, 24))
        btns = tk.Frame(center, bg=PLAYER_BG); btns.pack(pady=(10, 5))
        tk.Button(btns, image=self.ico_prev, bg=PLAYER_BG, activebackground=PLAYER_BG, bd=0, cursor="hand2", command=self.player.play_previous_song).pack(side="left", padx=15)
        self.btn_play = tk.Button(btns, image=self.ico_play, bg=PLAYER_BG, activebackground=PLAYER_BG, bd=0, cursor="hand2", command=self.player.toggle_playback); self.btn_play.pack(side="left", padx=15)
        tk.Button(btns, image=self.ico_skip, bg=PLAYER_BG, activebackground=PLAYER_BG, bd=0, cursor="hand2", command=self.player.skip_to_next).pack(side="left", padx=15)
        slider_f = tk.Frame(center, bg=PLAYER_BG); slider_f.pack(fill="x")
        self.lbl_cur = tk.Label(slider_f, text="0:00", bg=PLAYER_BG, fg=TEXT_COLOR, font=("Segoe UI", 9)); self.lbl_cur.pack(side="left")
        self.slider = ModernSlider(slider_f, width=400, height=50, command=lambda v: self.player.seek(float(v))); self.slider.pack(side="left", fill="x", expand=True, padx=10)
        self.lbl_tot = tk.Label(slider_f, text="0:00", bg=PLAYER_BG, fg=TEXT_COLOR, font=("Segoe UI", 9)); self.lbl_tot.pack(side="left")

        right = tk.Frame(bottom, bg=PLAYER_BG); right.grid(row=0, column=2, sticky="e", padx=20)
        tk.Button(right, text="+ Queue", bg=PLAYER_BG, fg=TEXT_COLOR, bd=0, font=("Segoe UI", 10), cursor="hand2", command=self.player.add_to_queue).pack()

    def update_gradient(self, event):
        w, h = event.width, event.height
        if w < 10: return
        self.grad_img = create_gradient(w, h, "#1E2A36", BG_COLOR) # Blue Gradient
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
            remaining = self.current_view_songs[index+1:]
            for s in remaining: self.player.add_to_queue(s)

    def refresh_list(self, songs, is_album=False):
        self.current_view_songs = songs
        frame = self.list_container.scrollable_frame
        for w in frame.winfo_children(): w.destroy()
        self._configure_grid_columns(frame)

        # HEADERS (Inside Grid)
        h_font = ("Segoe UI", 10, "bold")
        col0 = "#" if is_album else ""
        tk.Label(frame, text=col0, bg=BG_COLOR, fg="#6B7D8C", font=h_font).grid(row=0, column=0, sticky="w", pady=(0, 10), padx=(20, 0))
        tk.Label(frame, text="Title", bg=BG_COLOR, fg="#6B7D8C", font=h_font).grid(row=0, column=1, sticky="w", pady=(0, 10))
        tk.Label(frame, text="Album", bg=BG_COLOR, fg="#6B7D8C", font=h_font).grid(row=0, column=2, sticky="w", pady=(0, 10))
        tk.Label(frame, text="Duration", bg=BG_COLOR, fg="#6B7D8C", font=h_font).grid(row=0, column=3, sticky="e", pady=(0, 10), padx=(0, 20))
        
        sep = tk.Frame(frame, bg=SEPARATOR_COLOR, height=1)
        sep.grid(row=1, column=0, columnspan=4, sticky="ew", padx=20, pady=(0, 5))

        start_row = 2
        for i, song in enumerate(songs, start=start_row):
            r = i
            list_idx = i - start_row
            cmd = lambda e, idx=list_idx: self.play_song_from_view(idx)
            
            def on_ent(e, r=r):
                for w in frame.grid_slaves(row=r): w.config(bg=HOVER_COLOR)
            def on_lve(e, r=r):
                for w in frame.grid_slaves(row=r): w.config(bg=BG_COLOR)

            if is_album:
                l = tk.Label(frame, text=str(song.track_number), bg=BG_COLOR, fg=TEXT_COLOR)
                l.grid(row=r, column=0, sticky="w", pady=5, padx=(20, 0))
                l.bind("<Enter>", on_ent); l.bind("<Leave>", on_lve)
            else:
                if song.image_path:
                    icon = self.load_icon(song.image_path, (45, 45), rounded=True)
                    if icon:
                        self.image_refs[f"r{i}"] = icon
                        lbl = tk.Label(frame, image=icon, bg=BG_COLOR)
                        lbl.grid(row=r, column=0, sticky="w", pady=5, padx=(20, 0))
                        lbl.bind("<Button-1>", cmd); lbl.bind("<Enter>", on_ent); lbl.bind("<Leave>", on_lve)

            meta = tk.Frame(frame, bg=BG_COLOR)
            meta.grid(row=r, column=1, sticky="we", padx=5)
            t = tk.Label(meta, text=song.title, bg=BG_COLOR, fg=WHITE, font=("Segoe UI", 10, "bold"), anchor="w")
            t.pack(fill="x")
            a = tk.Label(meta, text=song.artist, bg=BG_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 9), anchor="w")
            a.pack(fill="x")
            for w in [meta, t, a]: w.bind("<Button-1>", cmd); w.bind("<Enter>", on_ent); w.bind("<Leave>", on_lve)

            l2 = tk.Label(frame, text=song.album, bg=BG_COLOR, fg=TEXT_COLOR, anchor="w")
            l2.grid(row=r, column=2, sticky="we")
            l2.bind("<Enter>", on_ent); l2.bind("<Leave>", on_lve)

            l3 = tk.Label(frame, text=_format_duration(song.duration), bg=BG_COLOR, fg=TEXT_COLOR, anchor="e")
            l3.grid(row=r, column=3, sticky="e", padx=(0, 20))
            l3.bind("<Enter>", on_ent); l3.bind("<Leave>", on_lve)

    def show_all_songs_view(self):
        self.header_canvas.itemconfig(self.title_text_id, text="All Songs")
        self.header_canvas.itemconfigure("controls", state="hidden")
        self.set_sidebar_active("all")
        self.refresh_list(self.library.get_sorted_song_list(), is_album=False)

    def show_albums_view(self):
        self.header_canvas.itemconfig(self.title_text_id, text="Albums")
        self.header_canvas.itemconfigure("controls", state="hidden")
        self.set_sidebar_active("albums")
        for w in self.list_container.scrollable_frame.winfo_children(): w.destroy()
        
        albums = self.library.get_songs_by_album()
        frame = self.list_container.scrollable_frame
        col, row = 0, 0
        for i, album in enumerate(albums):
            card = tk.Frame(frame, bg=BG_COLOR, width=180, height=220)
            card.grid(row=row, column=col, padx=15, pady=15)
            card.pack_propagate(False)
            songs = albums[album]
            if songs and songs[0].image_path:
                icon = self.load_icon(songs[0].image_path, (160, 160), rounded=True)
                if icon:
                    self.image_refs[f"alb{i}"] = icon
                    tk.Button(card, image=icon, bg=BG_COLOR, bd=0, activebackground=BG_COLOR, command=lambda a=album: self.open_album(a)).pack(pady=5)
            tk.Label(card, text=album, bg=BG_COLOR, fg=WHITE, font=("Segoe UI", 10, "bold"), wraplength=160).pack()
            col += 1
            if col > 3: col = 0; row += 1

    def open_album(self, album_name):
        self.header_canvas.itemconfig(self.title_text_id, text=album_name)
        self.header_canvas.itemconfigure("controls", state="normal")
        self.refresh_list(self.library.get_songs_by_album()[album_name], is_album=True)

    def play_current_view(self):
        if self.current_view_songs: 
            self.play_song_from_view(0)

    def shuffle_current_view(self):
        if self.current_view_songs:
            shuffled = list(self.current_view_songs)
            random.shuffle(shuffled)
            self.player.play_list(shuffled)

    def update_now_playing_ui(self, song):
        if song:
            self.lbl_mini_title.config(text=song.title)
            self.lbl_mini_artist.config(text=song.artist)
            self.lbl_tot.config(text=_format_duration(song.duration))
            self.slider.config_range(song.duration)
            self.btn_play.config(image=self.ico_pause)
            if song.image_path:
                icon = self.load_icon(song.image_path, (50, 50), rounded=True)
                if icon: self.image_refs["mini"] = icon; self.lbl_mini_art.config(image=icon)
        else:
            self.btn_play.config(image=self.ico_play)

    def update_queue_ui(self, queue):
        frame = self.queue_container.scrollable_frame
        for w in frame.winfo_children(): w.destroy()
        for i, song in enumerate(queue):
            bg = QUEUE_BG_1 if i % 2 == 0 else QUEUE_BG_2
            row = tk.Frame(frame, bg=bg, height=45)
            row.pack(fill="x", pady=0)
            row.pack_propagate(False)
            tk.Label(row, text=str(i+1), bg=bg, fg="#6B7D8C", width=4, font=("Segoe UI", 9)).pack(side="left", padx=(5,0))
            info = tk.Frame(row, bg=bg)
            info.pack(side="left", fill="x", expand=True, padx=5)
            tk.Label(info, text=song.title, bg=bg, fg=WHITE, font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x")
            tk.Label(info, text=song.artist, bg=bg, fg=TEXT_COLOR, font=("Segoe UI", 8), anchor="w").pack(fill="x")

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