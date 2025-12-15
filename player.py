def save_songs_to_file(library, filename="songs.txt"):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write("TITLE|ARTIST|ALBUM|TRACK|DURATION|GENRE|FILEPATH|IMAGE_PATH\n")
            for song in library.all_songs.values():
                line = "|".join(song.to_string())
                file.write(line + "\n")
        return f"Saved {len(library.all_songs)} songs."
    except Exception as e:
        return f"Error: {e}"

def load_songs_from_file(library, filename="songs.txt"):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            count = 0
            for line in lines[1:]:
                parts = line.strip().split('|')
                if len(parts) == 8:
                    title, artist, album, track, duration, genre, filepath, image_path = parts
                    try:
                        library.add_song(title, artist, album, int(track), int(duration), genre, filepath, image_path)
                        count += 1
                    except ValueError: pass
        return f"Loaded {count} songs."
    except FileNotFoundError:
        return "No save file found."