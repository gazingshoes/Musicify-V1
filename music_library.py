import math
from collections import defaultdict

def _format_duration(total_seconds):
    try:
        total_seconds = int(total_seconds)
        if total_seconds < 0: total_seconds = 0
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    except (ValueError, TypeError):
        return "0:00"

class MediaItem:
    def __init__(self, title, duration):
        self.title = title
        self.duration = duration
    def get_info(self):
        return f"{self.title} - {_format_duration(self.duration)}"

class Song(MediaItem):
    def __init__(self, title, artist, album, track_number, duration, genre, filepath, image_path):
        super().__init__(title, duration)
        self.artist = artist
        self.album = album
        self.track_number = track_number
        self.genre = genre
        self.filepath = filepath
        self.image_path = image_path
        self.__play_count = 0
        
    def play(self):
        self.__play_count += 1
    
    def get_play_count(self):
        return self.__play_count
    
    def get_info(self):
        return f"{self.track_number}. {self.title} - {self.artist}"
    
    def to_string(self):
        return (self.title, self.artist, self.album, str(self.track_number), str(self.duration), self.genre, self.filepath, self.image_path)

class MusicLibrary:
    def __init__(self):
        self.all_songs = {} 
        self.genres = set()
        self.albums = set()
        
    def add_song(self, title, artist, album, track_number, duration, genre, filepath, image_path):
        key = title.lower()
        if key in self.all_songs: return f"⚠️ Song '{title}' already exists!"
        
        new_song = Song(title, artist, album, track_number, duration, genre, filepath, image_path)
        self.all_songs[key] = new_song
        self.genres.add(genre)
        self.albums.add(album)
        return f"✅ Added song: {new_song.title}"
    
    def get_sorted_song_list(self):
        songs = list(self.all_songs.values())
        # Sort by Artist -> Album -> Track Number
        songs.sort(key=lambda s: (s.artist, s.album, s.track_number))
        return songs

    def get_songs_by_album(self):
        albums = defaultdict(list)
        for song in self.all_songs.values():
            albums[song.album].append(song)
        for album in albums:
            albums[album].sort(key=lambda s: s.track_number)
        return dict(sorted(albums.items()))

    def delete_song(self, title_input):
        key = title_input.lower()
        if key in self.all_songs:
            del self.all_songs[key]
            return True
        return False