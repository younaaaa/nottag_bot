import mutagen
from mutagen.mp3 import MP3, EasyMP3
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TRCK, TCON # and other relevant ID3 frames

class TagEditorService:
    def __init__(self, filepath):
        self.filepath = filepath
        try:
            self.audio = mutagen.File(filepath, easy=False) # easy=False for more control
            if self.audio is None:
                raise ValueError("Could not load file or unsupported file type")
        except Exception as e:
            # Log this error appropriately in a real scenario
            print(f"Error loading file {filepath}: {e}")
            raise ValueError(f"Error loading file: {e}")

    def get_tags(self):
        '''Reads a comprehensive set of tags from the loaded audio file.'''
        tags = {}
        if not self.audio:
            return tags

        if isinstance(self.audio, MP3):
            # Handling ID3 tags (often stored in self.audio.tags)
            for key in self.audio.tags:
                frame = self.audio.tags[key]
                # Example: extract text from common frames
                if hasattr(frame, 'text') and frame.text:
                    tags[key] = frame.text[0] if isinstance(frame.text, list) else frame.text
                # Add more specific frame handling if needed
            # Common tags often have easier accessors or are standard keys
            tags['title'] = self.audio.tags.get('TIT2', [None])[0]
            tags['artist'] = self.audio.tags.get('TPE1', [None])[0]
            tags['album'] = self.audio.tags.get('TALB', [None])[0]
            tags['year'] = str(self.audio.tags.get('TDRC', [None])[0]) if self.audio.tags.get('TDRC', [None])[0] else None
            tags['tracknumber'] = str(self.audio.tags.get('TRCK', [None])[0]) if self.audio.tags.get('TRCK', [None])[0] else None
            tags['genre'] = str(self.audio.tags.get('TCON', [None])[0]) if self.audio.tags.get('TCON', [None])[0] else None
        elif isinstance(self.audio, FLAC):
            for key, value in self.audio.tags:
                tags[key.lower()] = value[0] if isinstance(value, list) else value
        elif isinstance(self.audio, MP4):
            # MP4 tags use a different key format (e.g., '©nam' for title)
            tag_map = {
                '©nam': 'title',
                '©ART': 'artist',
                '©alb': 'album',
                '©day': 'year',
                'trkn': 'tracknumber', # Often a tuple (number, total)
                '©gen': 'genre',
            }
            for key_mp4, common_key in tag_map.items():
                if key_mp4 in self.audio:
                    value = self.audio[key_mp4]
                    if common_key == 'tracknumber' and isinstance(value, list) and len(value) > 0:
                        tags[common_key] = str(value[0][0]) if value[0] else None # track number is first element of first tuple
                    elif isinstance(value, list) and len(value) > 0:
                        tags[common_key] = str(value[0])
                    else:
                        tags[common_key] = str(value)


        # Normalize to common keys if possible, or decide on a standard set
        # For simplicity, this example uses the direct keys found or common ones
        # In a real app, you'd map these to a consistent internal representation.
        return {k: v for k, v in tags.items() if v is not None}


    def set_tag(self, tag_name, value):
        '''Sets a specific tag. tag_name should be a common name like 'title', 'artist'.'''
        if not self.audio:
            raise ValueError("Audio file not loaded")

        # This is a simplified example. Robust implementation needs mapping common names
        # to specific mutagen frame classes/keys for each file type.
        # For example:
        if isinstance(self.audio, MP3):
            # Ensure self.audio.tags exists (it's an ID3 object)
            if not self.audio.tags:
                self.audio.tags = ID3()

            if tag_name == 'title':
                self.audio.tags.add(TIT2(encoding=3, text=value))
            elif tag_name == 'artist':
                self.audio.tags.add(TPE1(encoding=3, text=value))
            elif tag_name == 'album':
                self.audio.tags.add(TALB(encoding=3, text=value))
            elif tag_name == 'year':
                self.audio.tags.add(TDRC(encoding=3, text=str(value)))
            elif tag_name == 'tracknumber':
                self.audio.tags.add(TRCK(encoding=3, text=str(value)))
            elif tag_name == 'genre':
                self.audio.tags.add(TCON(encoding=3, text=str(value)))
            # Add more tags as needed
        elif isinstance(self.audio, FLAC):
            # FLAC tags are key-value pairs (strings)
            self.audio.tags[tag_name.upper()] = str(value)
        elif isinstance(self.audio, MP4):
            # MP4 requires specific keys
            mp4_tag_map = {
                'title': '©nam',
                'artist': '©ART',
                'album': '©alb',
                'year': '©day',
                'tracknumber': 'trkn', # This might need special handling for (num, total)
                'genre': '©gen'
            }
            if tag_name in mp4_tag_map:
                mp4_key = mp4_tag_map[tag_name]
                if tag_name == 'tracknumber':
                    # Assuming value is just the track number. MP4 can store (track, total_tracks)
                    self.audio[mp4_key] = [(int(value), 0)] # Store as (track_num, 0) if total is unknown
                else:
                    self.audio[mp4_key] = [str(value)] # MP4 tags are often lists
            else:
                print(f"Unsupported MP4 tag: {tag_name}") # Or raise error
        else:
            print(f"Unsupported file type for setting tag: {tag_name}") # Or raise error


    def get_album_art(self):
        '''Retrieves album art (first one found) as bytes, or None.'''
        if not self.audio: return None

        if isinstance(self.audio, MP3) and self.audio.tags:
            pics = self.audio.tags.getall('APIC')
            if pics:
                return pics[0].data # return data of the first picture
        elif isinstance(self.audio, FLAC):
            if self.audio.pictures:
                return self.audio.pictures[0].data
        elif isinstance(self.audio, MP4):
            if '©cov' in self.audio and self.audio['©cov']:
                return self.audio['©cov'][0] # MP4Cover data is directly bytes
        return None

    def set_album_art(self, image_data, mime_type='image/jpeg'):
        '''Sets album art from image_data (bytes).'''
        if not self.audio: raise ValueError("Audio file not loaded")

        if isinstance(self.audio, MP3):
            if not self.audio.tags: self.audio.tags = ID3()
            # Remove existing APIC frames before adding new one
            self.audio.tags.delall('APIC')
            self.audio.tags.add(
                APIC(
                    encoding=3,  # 3 is for utf-8
                    mime=mime_type,
                    type=3,  # 3 is for cover front
                    desc='Cover',
                    data=image_data
                )
            )
        elif isinstance(self.audio, FLAC):
            # Remove existing pictures
            self.audio.clear_pictures()
            pic = Picture()
            pic.data = image_data
            pic.type = 3 # Front cover
            pic.mime = mime_type
            # pic.width = # optional
            # pic.height = # optional
            # pic.depth = # optional
            self.audio.add_picture(pic)
        elif isinstance(self.audio, MP4):
            # MP4 stores cover art in '©cov' tag, typically as a list of MP4Cover objects
            # Determine format based on mime_type
            fmt = MP4Cover.FORMAT_JPEG if mime_type == 'image/jpeg' else MP4Cover.FORMAT_PNG
            self.audio['©cov'] = [MP4Cover(image_data, imageformat=fmt)]
        else:
            print("Album art not supported for this file type via this method.")


    def save(self):
        '''Saves changes back to the file.'''
        if not self.audio:
            raise ValueError("Audio file not loaded or no changes to save.")
        self.audio.save()

# Example usage (for testing purposes, not part of the service file itself)
# if __name__ == '__main__':
#     # Create a dummy mp3 or flac for testing
#     # test_file = 'test.mp3'
#     # editor = TagEditorService(test_file)
#     # print(editor.get_tags())
#     # editor.set_tag('artist', 'New Artist')
#     # editor.save()
#     # print(editor.get_tags())
#     pass
