import math
from collections import defaultdict
import csv

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
    # Added play_count=0 to constructor
    def __init__(self, title, artist, album, track_number, duration, genre, filepath, image_path, is_liked=False, play_count=0):
        super().__init__(title, duration)
        self.artist = artist
        self.album = album
        self.track_number = track_number
        self.genre = genre
        self.filepath = filepath
        self.image_path = image_path
        self.is_liked = is_liked
        self.play_count = play_count # Public attribute now
        
    def play(self):
        self.play_count += 1
    
    def get_info(self):
        return f"{self.track_number}. {self.title} - {self.artist}"
    
    def to_string(self):
        # Save play_count at the end
        return (self.title, self.artist, self.album, str(self.track_number), 
                str(self.duration), self.genre, self.filepath, self.image_path, str(self.is_liked), str(self.play_count))

class MusicLibrary:
    def __init__(self):
        self.all_songs = {} 
        self.genres = set()
        self.albums = set()
        
    # Updated add_song to accept play_count
    def add_song(self, title, artist, album, track_number, duration, genre, filepath, image_path, is_liked=False, play_count=0):
        key = title.lower()
        if key in self.all_songs: 
            # Update existing song's volatile data
            self.all_songs[key].is_liked = is_liked
            self.all_songs[key].play_count = play_count
            return
        
        new_song = Song(title, artist, album, track_number, duration, genre, filepath, image_path, is_liked, play_count)
        self.all_songs[key] = new_song
        self.genres.add(genre)
        self.albums.add(album)
        return f"Added song: {new_song.title}"
    
    def get_sorted_song_list(self):
        songs = list(self.all_songs.values())
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
        
    def export_to_csv(self, filename):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Title", "Artist", "Album", "Track", "Duration", "Genre", "Filepath", "Image Path", "Liked", "Play Count"])
                for s in self.all_songs.values():
                    writer.writerow([s.title, s.artist, s.album, s.track_number, s.duration, s.genre, s.filepath, s.image_path, s.is_liked, s.play_count])
            return True
        except Exception as e:
            print(e)
            return False