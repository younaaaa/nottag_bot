from pydub import AudioSegment

def convert_format(input_file, output_file, target_format):
    """تبدیل فرمت فایل صوتی"""
    audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format=target_format)