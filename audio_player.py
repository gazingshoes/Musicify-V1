"""
Audio Player Module (Pygame Version)
This version uses pygame for playback and is integrated
with PySide6 by using QObject and Signals.
(FIXED to auto-play on add-to-queue if idle)
"""

import pygame
import time
from PySide6.QtCore import QObject, Signal

class AudioPlayer(QObject):
    """
    Manages audio playback using Pygame, but as a QObject
    to send signals to a PySide6 GUI.
    """
    # --- Signals ---
    current_song_changed = Signal(object) # object can be Song or None
    queue_changed = Signal(list) # Emits the new queue list

    def __init__(self):
        """
        Initialize the pygame mixer and the queue.
        """
        super().__init__() # Initialize as a QObject
        
        try:
            pygame.mixer.init()
            print("AudioPlayer initialized with Pygame.")
        except Exception as e:
            print(f"Error initializing Pygame mixer: {e}")
            
        self.queue = []
        self.history = []
        self.current_song = None
        self.is_playing = False
            
    def play_now(self, song):
        """
        Clears the queue, adds this song, and plays it immediately.
        """
        pygame.mixer.music.stop()
        self.queue = []
        self.queue.append(song)
        self.play_next_from_queue()
        self.queue_changed.emit(self.queue) # Emit signal
        
    def add_to_queue(self, song):
        """
        Adds a song to the end of the queue.
        If the player is idle, it will start playing.
        """
        self.queue.append(song)
        print(f"✅ Added '{song.title}' to queue.")
        self.queue_changed.emit(self.queue) # Emit signal
        
        # --- THIS IS THE NEW LOGIC ---
        # If nothing is playing, start the queue.
        if not self.is_playing and not pygame.mixer.music.get_busy():
            print("Player is idle, starting queue playback...")
            self.play_next_from_queue()
        # --- END OF NEW LOGIC ---

    def check_music_status(self):
        """
        This function is called by the QTimer in gui_main.py.
        It checks if a song has finished and triggers the next one.
        """
        # If our flag says we're playing, but pygame says we're not...
        if self.is_playing and not pygame.mixer.music.get_busy():
            # The song just finished!
            print("Song finished, playing next...")
            self.is_playing = False
            # Move finished song to history
            if self.current_song:
                self.history.append(self.current_song)
            self.current_song = None
            
            # Emit signal to clear "Now Playing" text
            self.current_song_changed.emit(None)
            
            # Immediately try to play the next song
            self.play_next_from_queue()

    def play_next_from_queue(self):
        """
        Plays the next song in the queue IF nothing is already playing.
        """
        # 1. If music is already playing, do nothing.
        if self.is_playing and pygame.mixer.music.get_busy():
            return

        # 2. If queue is empty, do nothing.
        if len(self.queue) == 0:
            return

        # 3. If we are here, music is not playing and queue has songs.
        #    Pop the next song and play it.
        song = self.queue.pop(0)
        self.current_song = song
        
        try:
            pygame.mixer.music.load(song.filepath)
            pygame.mixer.music.play()
            song.play() # This increments the play count
            self.is_playing = True # Set our flag
            print(f"▶️ Now playing: {self.current_song.title}")
            # --- Emit Signals ---
            self.current_song_changed.emit(self.current_song)
            self.queue_changed.emit(self.queue)
        except Exception as e:
            print(f"❌ Error playing file {song.filepath}: {e}")
            self.is_playing = False
            
    def skip_to_next(self):
        """
        Stops the current song and immediately plays the next one in the queue.
        """
        print("⏭️ Skipping to next song...")
        pygame.mixer.music.stop()
        
        # Manually add the skipped song to history
        if self.current_song:
            self.history.append(self.current_song)
        self.current_song = None
        
        self.is_playing = False
        self.play_next_from_queue() # This will now just play the next item

    def play_previous_song(self):
        """
        Stops the current song, moves it back to the queue,
        and plays the *last* song from the history.
        """
        if len(self.history) == 0:
            print("❌ No previous song in history.")
            return
            
        print("⏮️ Playing previous song...")
        pygame.mixer.music.stop()
        
        # Put the current song back at the front of the queue
        if self.current_song:
            self.queue.insert(0, self.current_song)
        self.current_song = None
            
        prev_song = self.history.pop()
        self.queue.insert(0, prev_song)
        
        self.is_playing = False
        self.play_next_from_queue()

    def stop(self):
        """
        Stops the music and clears the entire queue and history.
        """
        self.queue = []
        self.history = []
        self.current_song = None
        pygame.mixer.music.stop()
        self.is_playing = False
        print("⏹️ Music stopped and queue/history cleared.")
        # --- Emit Signals ---
        self.current_song_changed.emit(None)
        self.queue_changed.emit(self.queue)