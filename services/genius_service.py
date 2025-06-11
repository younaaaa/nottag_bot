import lyricsgenius
from config import Config # Assuming Config has GENIUS_ACCESS_TOKEN
import re # For cleaning lyrics

class GeniusService:
    def __init__(self):
        if not Config.GENIUS_ACCESS_TOKEN:
            raise ValueError("GENIUS_ACCESS_TOKEN not set in Config. Please set it in your .env file.")

        # lyricsgenius can be verbose with status messages, can disable if needed
        self.genius_api = lyricsgenius.Genius(
            Config.GENIUS_ACCESS_TOKEN,
            verbose=False, # Suppress status messages
            remove_section_headers=True, # Remove headers like [Chorus], [Verse], etc.
            skip_non_songs=True, # Skip things like interviews, articles
            excluded_terms=["(Remix)", "(Live)"] # Exclude certain terms from titles
        )

    def search_lyrics(self, title, artist):
        '''
        Searches for lyrics for a given song title and artist.

        :param title: The title of the song.
        :param artist: The artist of the song.
        :return: A string containing the lyrics, or None if not found or an error occurs.
        '''
        if not title or not artist:
            return None

        try:
            song = self.genius_api.search_song(title, artist)
            if song and song.lyrics:
                # Clean up lyrics a bit:
                # - Remove the typical "EmbedShare URLCopyEmbedCopy" that sometimes appears
                # - Normalize line endings if necessary (though lyricsgenius usually handles this)
                lyrics_text = song.lyrics
                lyrics_text = lyrics_text.replace("EmbedShare URLCopyEmbedCopy", "").strip()

                # Remove the first line if it's just the song title and artist (Genius often adds this)
                lines = lyrics_text.split('\n')
                if len(lines) > 1 and lines[0].strip().lower().startswith(title.lower()):
                     # Check if the first line is similar to "Song Title Lyrics"
                    if "lyrics" in lines[0].lower() or artist.lower() in lines[0].lower():
                       lyrics_text = "\n".join(lines[1:]).strip()

                # Also remove the "You might also like" part and the number that sometimes appears at the end.
                # Example: "123Embed" or "Source: LyricFind12Embed"
                lyrics_lines = lyrics_text.split('\n')
                cleaned_lines = []
                # Stop adding lines once "you might also like" is encountered
                stop_phrases = ["you might also like", "you may also like"]
                for i, line in enumerate(lyrics_lines):
                    if any(stop_phrase in line.lower() for stop_phrase in stop_phrases):
                        break

                    # Check for typical Genius footer patterns like "NEmbed" or "Source: ...NEmbed"
                    # This regex is a bit naive but tries to catch common cases.
                    # Only remove if it's the last line among the currently considered lines (before potential "You might also like")
                    if (re.match(r"^\d*Embed$", line.strip()) or \
                        re.match(r"^Source:.*?\d*Embed$", line.strip()) or \
                        re.match(r"^.*?Lyrics\d*Embed$", line.strip())) and \
                        (i == len(lyrics_lines) - 1 or any(stop_phrase in lyrics_lines[i+1].lower() for stop_phrase in stop_phrases)):
                        break
                    cleaned_lines.append(line)

                lyrics_text = "\n".join(cleaned_lines).strip()

                return lyrics_text
            else:
                return None # Song not found or lyrics are empty
        except Exception as e:
            # This can include network errors, API rate limits, etc.
            print(f"Error searching lyrics on Genius for '{title}' by '{artist}': {e}")
            return None # Indicate error

# Example Usage (for testing, not part of the service file)
# if __name__ == '__main__':
#     # Make sure .env has GENIUS_ACCESS_TOKEN
#     # from dotenv import load_dotenv
#     # load_dotenv() # To load .env for local testing
#
#     genius_service = GeniusService()
#     song_title = "Bohemian Rhapsody"
#     song_artist = "Queen"
#     lyrics = genius_service.search_lyrics(song_title, song_artist)
#
#     if lyrics:
#         print(f"Lyrics for '{song_title}' by '{song_artist}':\n---")
#         print(lyrics)
#         print("---")
#     else:
#         print(f"Could not find lyrics for '{song_title}' by '{song_artist}'.")
#
#     song_title_nonexist = "Super Fictional Song"
#     song_artist_nonexist = "The Imaginary Band"
#     lyrics_nonexist = genius_service.search_lyrics(song_title_nonexist, song_artist_nonexist)
#     if not lyrics_nonexist:
#         print(f"Correctly did not find lyrics for '{song_title_nonexist}' by '{song_artist_nonexist}'.")
#
#     # Test with a song that might have "You might also like" and embed footers
#     # song_title_complex = "Yesterday"
#     # song_artist_complex = "The Beatles"
#     # lyrics_complex = genius_service.search_lyrics(song_title_complex, song_artist_complex)
#     # if lyrics_complex:
#     #     print(f"\nLyrics for '{song_title_complex}' by '{song_artist_complex}':\n---")
#     #     print(lyrics_complex)
#     #     print("---")
#     # else:
#     #     print(f"Could not find lyrics for '{song_title_complex}' by '{song_artist_complex}'.")
