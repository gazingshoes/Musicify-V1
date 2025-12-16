import os

def save_songs_to_file(library, filename="songs.txt"):
    try:
        # 1. Generate data in memory FIRST
        lines_to_write = []
        # Header now includes PLAY_COUNT
        lines_to_write.append("TITLE|ARTIST|ALBUM|TRACK|DURATION|GENRE|FILEPATH|IMAGE_PATH|IS_LIKED|PLAY_COUNT\n")
        
        for song in library.all_songs.values():
            lines_to_write.append("|".join(song.to_string()) + "\n")

        # 2. Open the file ONLY if step 1 succeeded
        with open(filename, 'w', encoding='utf-8') as file:
            file.writelines(lines_to_write)
        return f"Saved {len(library.all_songs)} songs."
    except Exception as e:
        print(f"⚠️ CRITICAL SAVE ERROR (File not touched): {e}")
        return f"Error: {e}"

def load_songs_from_file(library, filename="songs.txt"):
    try:
        if not os.path.exists(filename): return "No save file found."
        
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            count = 0
            for line in lines[1:]:
                parts = line.strip().split('|')
                # We need at least 8 parts for the basic app to work
                if len(parts) >= 8:
                    title = parts[0]
                    artist = parts[1]
                    album = parts[2]
                    track = parts[3]
                    duration = parts[4]
                    genre = parts[5]
                    filepath = parts[6]
                    image_path = parts[7]
                    
                    # Safe Loading for Liked Status
                    is_liked = False
                    if len(parts) > 8:
                        is_liked = (parts[8] == "True")
                        
                    # Safe Loading for Play Count
                    play_count = 0
                    if len(parts) > 9:
                        try: play_count = int(parts[9])
                        except: play_count = 0

                    try:
                        library.add_song(title, artist, album, int(track), int(duration), genre, filepath, image_path, is_liked, play_count)
                        count += 1
                    except ValueError: pass
                    except Exception as e: print(f"Error loading line: {e}")
                    
        return f"Loaded {count} songs."
    except Exception as e:
        return f"Load Error: {e}"