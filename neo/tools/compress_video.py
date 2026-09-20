import os
from moviepy import VideoFileClip   # moviepy 2.x API (moviepy.editor was removed)

def compress_video(input_file, output_file):
    try:
        video = VideoFileClip(input_file)
        video.write_videofile(output_file, codec="libx264", audio_codec="aac", logger=None)
        video.close()
        return '✅ Success: Video compressed and saved to ' + output_file
    except Exception as e:
        return '❌ Error: ' + str(e)

# Example usage:
# print(compress_video('input.mp4', 'output.mp4'))