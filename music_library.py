"""
Music Library Module (UPGRADED)
Contains classes for Song and MusicLibrary
Now with helper functions to get categorized data for the GUI.
"""
import math
from collections import defaultdict # We need this

# --- HELPER FUNCTION ---
def _format_duration(total_seconds):
    """Converts total seconds into an M:SS string."""
    try:
        total_seconds = int(total_seconds)
        if total_seconds < 0:
            total_seconds = 0
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    except (ValueError, TypeError):
        return "0:00"

# --- MediaItem Class (Unchanged) ---
class MediaItem:
    def __init__(self, title, duration):
        self.title = title
        self.duration = duration
    def get_info(self):
        return f"{self.title} - {_format_duration(self.duration)}"

# --- Song Class (Unchanged) ---
class Song(MediaItem):
    def __init__(self, title, artist, duration, genre, filepath):
        super().__init__(title, duration)
        self.artist = artist
        self.genre = genre
        self.filepath = filepath
        self.__play_count = 0
    def play(self):
        self.__play_count += 1
        return f"🎵 Incrementing play count for: {self.title}"
    def get_play_count(self):
        return self.__play_count
    def get_info(self):
        duration_str = _format_duration(self.duration)
        return f"{self.title} - {self.artist} ({self.genre}) [{duration_str}]"
    def to_string(self):
        return (self.title, self.artist, str(self.duration), self.genre, self.filepath)

# --- MusicLibrary Class (UPDATED) ---
class MusicLibrary:
    def __init__(self):
        self.all_songs = {} # Key: "konservatif", Value: Song(...)
        self.genres = set()
        
    def add_song(self, title, artist, duration, genre, filepath):
        key = title.lower()
        if key in self.all_songs:
            return f"⚠️ Song '{title}' already exists in library!"
        new_song = Song(title, artist, duration, genre, filepath)
        self.all_songs[key] = new_song
        self.genres.add(genre)
        return f"✅ Added song: {new_song.get_info()}"
    
    def get_song(self, title_input):
        key = title_input.lower()
        song = self.all_songs.get(key)
        if song:
            return song
        for song_key, song_obj in self.all_songs.items():
            if song_key.startswith(key):
                return song_obj
        return None
    
    def search_by_artist(self, artist_input):
        query_lower = artist_input.lower()
        results = [song for song in self.all_songs.values() 
                   if query_lower in song.artist.lower()]
        return results
    
    def search_by_genre(self, genre_input):
        query_lower = genre_input.lower()
        results = [song for song in self.all_songs.values() 
                   if query_lower in song.genre.lower()]
        return results
    
    def show_all_songs(self):
        if len(self.all_songs) == 0:
            return "🎵 Library is empty! Add some songs first."
        result = f"\n{'='*60}\nALL SONGS IN LIBRARY\n{'='*60}\n"
        sorted_keys = sorted(self.all_songs.keys())
        for index, key in enumerate(sorted_keys, start=1):
            song = self.all_songs[key]
            result += f"{index}. {song.get_info()} [Played: {song.get_play_count()}x]\n"
        return result
    
    def get_all_genres(self):
        return sorted(list(self.genres))

    def edit_song(self, song, field_to_edit, new_value):
        try:
            if field_to_edit == "title":
                old_key = song.title.lower()
                new_key = new_value.lower()
                if old_key == new_key:
                    song.title = new_value
                    return f"✅ Title capitalization updated for '{new_value}'."
                if new_key in self.all_songs:
                    return f"❌ Edit failed. A song with title '{new_value}' already exists."
                song.title = new_value
                del self.all_songs[old_key]
                self.all_songs[new_key] = song
                return f"✅ Title updated to '{new_value}'."
            elif field_to_edit == "artist":
                song.artist = new_value
                return f"✅ Artist updated to '{new_value}'."
            elif field_to_edit == "duration":
                song.duration = int(new_value)
                return f"✅ Duration updated to '{_format_duration(new_value)}'."
            elif field_to_edit == "genre":
                song.genre = new_value
                return f"✅ Genre updated to '{new_value}'."
            elif field_to_edit == "filepath":
                song.filepath = new_value
                return f"✅ Filepath updated for '{song.title}'."
        except ValueError:
            return "❌ Edit failed. Duration must be a number."
        except Exception as e:
            return f"❌ An unexpected error occurred: {e}"

    def delete_song(self, title_input):
        song = self.get_song(title_input)
        if not song:
            return f"❌ Song '{title_input}' not found."
        key = song.title.lower()
        del self.all_songs[key]
        return f"✅ Successfully deleted '{song.title}' from the library."

    def get_sorted_song_list(self):
        sorted_keys = sorted(self.all_songs.keys())
        return [self.all_songs[key] for key in sorted_keys]

    # --- NEW HELPER 1 ---
    def get_songs_by_artist(self):
        """Returns a dict of songs grouped by artist."""
        artists = defaultdict(list)
        for song in self.all_songs.values():
            artists[song.artist].append(song)
        # Sort songs alphabetically within each artist
        for artist in artists:
            artists[artist].sort(key=lambda s: s.title.lower())
        return dict(sorted(artists.items()))

    # --- NEW HELPER 2 ---
    def get_songs_by_genre(self):
        """Returns a dict of songs grouped by genre."""
        genres = defaultdict(list)
        for song in self.all_songs.values():
            genres[song.genre].append(song)
        # Sort songs alphabetically within each genre
        for genre in genres:
            genres[genre].sort(key=lambda s: s.title.lower())
        return dict(sorted(genres.items()))