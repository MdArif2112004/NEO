import moviepy.editor as mp
import os

def compress_video(input_file, output_file):
    try:
        video = mp.VideoFileClip(input_file)
        video.write_videofile(output_file, codec="libx264", audio_codec="aac", verbose=False)
        video.close()
        return '✅ Success: Video compressed and saved to ' + output_file
    except Exception as e:
        return '❌ Error: ' + str(e)

# Example usage:
# print(compress_video('input.mp4', 'output.mp4'))