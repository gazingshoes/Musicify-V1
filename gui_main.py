"""
main program to run (gui)
this loads its layout from 'mainwindow.ui'
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QPushButton, 
    QListWidgetItem, QTabWidget, QTreeWidget, QTreeWidgetItem, QLabel
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QTimer, QFile, QIODevice, QObject, Slot

# --- Import all our existing logic ---
from music_library import MusicLibrary, Song, _format_duration
from player import (load_songs_from_file, save_songs_to_file)
from audio_player import AudioPlayer

# This class is now a "controller" not a "window"
class MainWindowController(QObject):
    """
    The main application CONTROLLER.
    Loads the UI from mainwindow.ui and connects the logic.
    """
    def __init__(self, library, player, app):
        super().__init__()
        
        self.library = library
        self.player = player
        
        # --- Load the UI file ---
        ui_file = QFile("mainwindow.ui")
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open UI file: {ui_file.errorString()}")
            sys.exit(-1)
        
        # We don't need to keep the loader
        loader = QUiLoader()
        # Load the window (it's a QMainWindow) and store it
        self.window = loader.load(ui_file)
        ui_file.close()
        
        if not self.window:
            print(f"Failed to load UI file: {loader.errorString()}")
            sys.exit(-1)

        # --- Find all the widgets by their name ---
        self.tab_widget = self.window.findChild(QTabWidget, "tabWidget")
        self.song_list_widget = self.window.findChild(QListWidget, "songListWidget")
        self.artist_tree_widget = self.window.findChild(QTreeWidget, "artistTreeWidget")
        self.genre_tree_widget = self.window.findChild(QTreeWidget, "genreTreeWidget")
        
        # Player Controls
        self.prev_button = self.window.findChild(QPushButton, "prevButton")
        self.skip_button = self.window.findChild(QPushButton, "skipButton")
        self.stop_button = self.window.findChild(QPushButton, "stopButton")
        
        # Action Buttons
        self.play_selected_button = self.window.findChild(QPushButton, "playSelectedButton")
        self.add_queue_button = self.window.findChild(QPushButton, "addQueueButton")
        
        # Queue/Sidebar
        self.now_playing_label = self.window.findChild(QLabel, "nowPlayingLabel")
        self.queue_list_widget = self.window.findChild(QListWidget, "queueListWidget")
        self.clear_queue_button = self.window.findChild(QPushButton, "clearQueueButton")
        
        # --- Connect Buttons to Functions (Signals & Slots) ---
        self.play_selected_button.clicked.connect(self.play_selected)
        self.add_queue_button.clicked.connect(self.add_selected_to_queue)
        self.clear_queue_button.clicked.connect(self.player.stop)
        
        self.skip_button.clicked.connect(self.player.skip_to_next)
        self.prev_button.clicked.connect(self.player.play_previous_song)
        self.stop_button.clicked.connect(self.player.stop)
        
        # Double-clicking
        self.song_list_widget.itemDoubleClicked.connect(self.play_selected)
        self.artist_tree_widget.itemDoubleClicked.connect(self.play_from_tree)
        self.genre_tree_widget.itemDoubleClicked.connect(self.play_from_tree)

        # --- Connect AudioPlayer SIGNALS to GUI SLOTS ---
        self.player.current_song_changed.connect(self.update_now_playing)
        self.player.queue_changed.connect(self.update_queue_list)
        
        # --- Connect App-level "quit" signal to our save function ---
        app.aboutToQuit.connect(self.on_close)
        
        # --- Populate all lists ---
        self.refresh_all_lists()

        # --- Setup Playback Timer ---
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.player.check_music_status) 
        self.playback_timer.start(100) # 100 milliseconds

    def show(self):
        """Call this to show the window."""
        self.window.show()

    # --- GUI Population Functions ---
    def refresh_all_lists(self):
        self.populate_all_songs()
        self.populate_artist_tree()
        self.populate_genre_tree()

    def populate_all_songs(self):
        self.song_list_widget.clear()
        for song in self.library.get_sorted_song_list():
            list_item = QListWidgetItem(song.get_info())
            list_item.setData(Qt.ItemDataRole.UserRole, song)
            self.song_list_widget.addItem(list_item)
            
    def populate_artist_tree(self):
        self.artist_tree_widget.clear()
        artists = self.library.get_songs_by_artist()
        for artist_name, songs in artists.items():
            artist_item = QTreeWidgetItem([artist_name])
            self.artist_tree_widget.addTopLevelItem(artist_item)
            for song in songs:
                song_item = QTreeWidgetItem([song.get_info()])
                song_item.setData(0, Qt.ItemDataRole.UserRole, song)
                artist_item.addChild(song_item)
                
    def populate_genre_tree(self):
        self.genre_tree_widget.clear()
        genres = self.library.get_songs_by_genre()
        for genre_name, songs in genres.items():
            genre_item = QTreeWidgetItem([genre_name])
            self.genre_tree_widget.addTopLevelItem(genre_item)
            for song in songs:
                song_item = QTreeWidgetItem([song.get_info()])
                song_item.setData(0, Qt.ItemDataRole.UserRole, song)
                # --- THIS IS THE FIX ---
                genre_item.addChild(song_item) # Was 'artist_item'

    # --- GUI Action Functions ---
    def get_selected_song(self):
        current_tab_index = self.tab_widget.currentIndex()
        
        if current_tab_index == 0:
            selected_item = self.song_list_widget.currentItem()
        elif current_tab_index == 1:
            selected_item = self.artist_tree_widget.currentItem()
        elif current_tab_index == 2:
            selected_item = self.genre_tree_widget.currentItem()
        else:
            return None
            
        if selected_item:
            if isinstance(selected_item, QListWidgetItem):
                song = selected_item.data(Qt.ItemDataRole.UserRole)
            else:
                song = selected_item.data(0, Qt.ItemDataRole.UserRole)
            
            if isinstance(song, Song):
                return song
        return None

    def play_selected(self):
        song = self.get_selected_song()
        if song:
            self.player.play_now(song)
            print(f"Play Now: {song.title}")

    def add_selected_to_queue(self):
        song = self.get_selected_song()
        if song:
            self.player.add_to_queue(song)
            print(f"Added to Queue: {song.title}")

    def play_from_tree(self, item, column):
        song = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(song, Song):
            self.player.play_now(song)
            print(f"Play Now: {song.title}")

    # --- GUI Update SLOTS (Called by signals) ---
    @Slot(object) # Use @Slot decorator for type safety
    def update_now_playing(self, song):
        if song:
            self.now_playing_label.setText(f"Now Playing:\n{song.title}")
        else:
            self.now_playing_label.setText("Now Playing: (Nothing)")

    @Slot(list) # Use @Slot decorator for type safety
    def update_queue_list(self, queue):
        self.queue_list_widget.clear()
        for song in queue:
            item_text = f"{song.title} - {song.artist}"
            self.queue_list_widget.addItem(item_text)

    # --- Save Function (Called on exit) ---
    @Slot() # This is a slot for the app.aboutToQuit signal
    def on_close(self):
        """
        This function is called when the user closes the window.
        """
        print(save_songs_to_file(self.library))
        print("\n✅ Data saved. Goodbye!")

# ===================================================================
# --- MAIN APPLICATION STARTUP ---
# ===================================================================
def main():
    app = QApplication(sys.argv)
    
    library = MusicLibrary()
    print(load_songs_from_file(library))
    
    player = AudioPlayer()
    
    # Pass the 'app' instance to the controller
    controller = MainWindowController(library, player, app)
    controller.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()