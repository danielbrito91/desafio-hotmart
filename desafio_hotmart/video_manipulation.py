from moviepy.editor import AudioFileClip, VideoFileClip


def video_to_audio(
    video_path: str,
    audio_path: str,
    subclip_start_seconds: int = 0,
    subclip_end_seconds: int = 245,
) -> None:
    """
    Convert a video file to an audio file.

    Args:
        video_path (str): The path to the video file.
        audio_path (str): The path to save the audio file.
        subclip_start_seconds (int, optional): The start time of the subclip in seconds. Defaults to 0.
        subclip_end_seconds (int, optional): The end time of the subclip in seconds. Defaults to 245.
    """
    clip = VideoFileClip(video_path)
    sample_clip = clip.subclip(subclip_start_seconds, subclip_end_seconds)
    audio = sample_clip.audio
    audio.write_audiofile(audio_path)
    clip.close()


def replace_audio(
    video_path: str,
    audio_path: str,
    output_video_path: str,
    subclip_start_seconds: int = 0,
    subclip_end_seconds: int = 245,
) -> None:
    """
    Replace the audio of a video file with another audio file.

    Args:
        video_path (str): The path to the video file.
        audio_path (str): The path to the audio file.
        output_video_path (str): The path to save the video file with the new audio.
        subclip_start_seconds (int, optional): The start time of the subclip in seconds. Defaults to 0.
        subclip_end_seconds (int, optional): The end time of the subclip in seconds. Defaults to 245.
    """
    clip = VideoFileClip(video_path)
    sample_clip = clip.subclip(subclip_start_seconds, subclip_end_seconds)
    new_audio = AudioFileClip(audio_path)
    sample_clip = sample_clip.set_audio(new_audio)
    sample_clip.write_videofile(output_video_path)
    clip.close()
    new_audio.close()
