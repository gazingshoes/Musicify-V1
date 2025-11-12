"""
Player Module
Handles file operations for songs.
"""

def save_songs_to_file(library, filename="songs.txt"):
    """
    Save all songs to a text file
    Uses: File handling (write mode), Exception handling, Loops
    """
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write("TITLE|ARTIST|DURATION|GENRE|FILEPATH\n")
            
            for song in library.all_songs.values():
                song_data = song.to_string()
                line = "|".join(song_data)
                file.write(line + "\n")
        
        return f"✅ Saved {len(library.all_songs)} songs to {filename}"
    
    except IOError as e:
        return f"❌ Error saving file: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"


def load_songs_from_file(library, filename="songs.txt"):
    """
    Load songs from a text file
    Uses: File handling (read mode), Exception handling
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
            count = 0
            for line in lines[1:]:
                parts = line.strip().split('|')
                
                if len(parts) == 5:
                    title, artist, duration, genre, filepath = parts
                    try:
                        library.add_song(title, artist, int(duration), genre, filepath)
                        count += 1
                    except ValueError:
                         print(f"Skipping song with invalid duration: {title}")
                else:
                    print(f"Skipping malformed line: {line.strip()}")
        
        return f"✅ Loaded {count} songs from {filename}"
    
    except FileNotFoundError:
        return f"⚠️ File '{filename}' not found. Starting with empty library."
    except ValueError as e:
        return f"❌ Error reading file data: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"