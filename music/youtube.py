from pytube import YouTube

def download_audio(url):
    """دانلود فایل صوتی از YouTube"""
    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    return stream.download(output_path="downloads/")