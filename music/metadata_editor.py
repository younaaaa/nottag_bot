from mutagen.easyid3 import EasyID3

def edit_metadata(file_path, title=None, artist=None, album=None):
    """ویرایش متادیتا فایل صوتی"""
    audio = EasyID3(file_path)
    if title:
        audio["title"] = title
    if artist:
        audio["artist"] = artist
    if album:
        audio["album"] = album
    audio.save()