"""
Audio Player Module (Tkinter Version)
Fixed: Prev button logic (Restart if > 10s, Prev if < 10s).
"""
import pygame
import random

class AudioPlayer:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=44100) 
        except Exception as e:
            print(f"Error initializing Pygame mixer: {e}")
            
        self.queue = []
        self.history = []
        self.current_song = None
        self.is_playing = False 
        self.is_paused = False
        self.current_pos_offset = 0.0 
        
        # Callbacks
        self.on_song_changed = None 
        self.on_queue_changed = None
        self.on_playback_state_changed = None

    def play_now(self, song):
        self.stop()
        self.queue = []
        self.queue.append(song)
        self.play_next_from_queue()
        if self.on_queue_changed: self.on_queue_changed(self.queue)

    def play_list(self, songs, start_index=0):
        self.stop()
        self.queue = list(songs)
        if self.queue:
            self.play_next_from_queue()
        if self.on_queue_changed: self.on_queue_changed(self.queue)

    def add_to_queue(self, song):
        self.queue.append(song)
        if self.on_queue_changed: self.on_queue_changed(self.queue)
        if not self.is_playing and not self.is_paused:
            self.play_next_from_queue()

    def clear_queue(self):
        self.queue = []
        if self.on_queue_changed: self.on_queue_changed(self.queue)

    def shuffle_queue(self):
        random.shuffle(self.queue)
        if self.on_queue_changed: self.on_queue_changed(self.queue)

    def check_music_status(self):
        if self.is_playing and not self.is_paused:
            if not pygame.mixer.music.get_busy():
                print("Song finished naturally.")
                self.is_playing = False
                self.is_paused = False
                if self.current_song:
                    self.history.append(self.current_song)
                self.current_song = None
                
                if self.on_song_changed: self.on_song_changed(None)
                self.play_next_from_queue()

    def play_next_from_queue(self):
        if self.is_playing: return
        if len(self.queue) == 0: return

        song = self.queue.pop(0)
        self.current_song = song
        
        try:
            pygame.mixer.music.load(song.filepath)
            self.current_pos_offset = 0.0
            pygame.mixer.music.play()
            song.play()
            self.is_playing = True
            self.is_paused = False
            
            if self.on_song_changed: self.on_song_changed(self.current_song)
            if self.on_queue_changed: self.on_queue_changed(self.queue)
            if self.on_playback_state_changed: self.on_playback_state_changed(True)
        except Exception as e:
            print(f"Error playing file: {e}")
            self.is_playing = False
            self.play_next_from_queue()

    def toggle_playback(self):
        if not self.current_song: return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True
            if self.on_playback_state_changed: self.on_playback_state_changed(True)
        elif self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            if self.on_playback_state_changed: self.on_playback_state_changed(False)

    def seek(self, seconds):
        if self.current_song:
            try:
                pygame.mixer.music.play(start=seconds)
                self.current_pos_offset = seconds
                self.is_playing = True
                self.is_paused = False
                if self.on_playback_state_changed: self.on_playback_state_changed(True)
            except Exception as e:
                print(f"Seek error: {e}")

    def get_current_position(self):
        if not self.current_song: return 0
        try:
            pygame_pos_seconds = pygame.mixer.music.get_pos() / 1000.0
            if pygame_pos_seconds < 0: return self.current_pos_offset
            return self.current_pos_offset + pygame_pos_seconds
        except:
            return 0

    def skip_to_next(self):
        self.stop()
        if self.current_song: self.history.append(self.current_song)
        self.current_song = None
        self.play_next_from_queue()

    def play_previous_song(self):
        # --- LOGIC FIX ---
        # If playing > 10s: Restart
        # Else: Go to previous song
        if self.is_playing and self.get_current_position() > 10.0:
            self.seek(0.0)
        else:
            if len(self.history) == 0: return
            self.stop()
            if self.current_song: self.queue.insert(0, self.current_song)
            self.current_song = None
            prev_song = self.history.pop()
            self.queue.insert(0, prev_song)
            self.play_next_from_queue()

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_pos_offset = 0.0
        if self.on_playback_state_changed: self.on_playback_state_changed(False)