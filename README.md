# Project Pemdas - Musicify V2

Now with a GUI! Made using QTDesigner (pySide6)

## How to Use

Run `gui_main.py` and follow the instructions in the Main Menu.

There's already a provided list of songs in `songs.txt`. You can:
* Edit, add, or remove songs directly in `songs.txt` (before running the program).
* Use the features in the "Library" menu while the program is running.

**Important Note:** For the music playback to work, you **have** to provide the **full, correct file path** to your `.mp3` or `.wav` files when adding or editing songs. The program needs this exact path to find and play the music.

**Also a very Important Note:** The provided `songs.txt` can't be actually played, if you don't have the songs and the **exact** path for them, so please do change the contents of it to your liking!

Example path:
* macOS/Linux: `/Users/your_username/Music/song_name.mp3`
* Windows: `C:\Users\your_username\Music\song_name.mp3`

---

## Project Files

Breakdown of the file path:

* `main.py`
    * **Notes:** This is the main file you run to start the application. Handles the terminal menus and user interactions.
* `music_library.py`
    * **Notes:** Contains the "brain" of the library. Defines the `Song` class to hold song data and the `MusicLibrary` class to manage all songs (add, edit, delete, search).
* `audio_player.py`
    * **Notes:** Manages the actual music playback using the `pygame` library. It also handles the song queue (adding songs, playing the next song).
* `player.py`
    * **Notes:** Contains functions for saving the current song list to `songs.txt` and loading songs from `songs.txt` when the program starts.
* `songs.txt`
    * **Notes:** The data file where your song information is stored (with the format).
* `.gitignore`
    * **Notes:** This is not important, it's just to prevent `__pycache__` folder to be pushed to github.
