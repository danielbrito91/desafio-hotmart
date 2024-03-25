import yaml

from desafio_hotmart.speech_to_text import ASR
from desafio_hotmart.text_to_speech import TextToSpeech
from desafio_hotmart.translate import Translator
from desafio_hotmart.video_manipulation import replace_audio, video_to_audio

if __name__ == "__main__":
    with open("params.yaml") as f:
        config = yaml.safe_load(f)

    # Convert video to audio
    print("Converting video to audio...")
    video_to_audio(
        config["data"]["input"]["video"],
        config["data"]["intermediate"]["original_audio"],
        config["base"]["subclip_start_seconds"],
        config["base"]["subclip_end_seconds"],
    )

    # Transcribe the audio to text
    print("Transcribing audio to text...")
    asr = ASR(
        config["data"]["intermediate"]["original_audio"],
        config["data"]["output"]["transcribed_text_with_timestamps"],
        config["data"]["output"]["transcribed_text"],
        config["model"]["asr"],
    )
    transcription = asr.speech_to_text()
    asr.export_transcription(transcription)

    # Translate the transcription from Portuguese to English
    print("Translating text...")
    translator = Translator(
        config["data"]["output"]["transcribed_text_with_timestamps"],
        config["model"]["translator"],
        config["data"]["output"]["translated_text_with_timestamps"],
        config["data"]["output"]["translated_text"],
    )
    translated_text = translator.translate_chunks()
    translator.export_translation(translated_text)

    # # Convert the translated text to speech
    print("Converting text to speech...")
    tts = TextToSpeech(
        config["data"]["output"]["translated_text_with_timestamps"],
        config["data"]["output"]["translated_audio"],
        config["model"]["tts"],
        config["data"]["intermediate"]["original_audio"],
    )
    translated_audio = tts.convert_chunks_to_speech()
    tts.export_audio(translated_audio, False)

    # Replace the audio of the video with the translated audio
    print("Replacing audio in video...")
    replace_audio(
        config["data"]["input"]["video"],
        config["data"]["output"]["translated_audio"],
        config["data"]["output"]["voice_over_video"],
        config["base"]["subclip_start_seconds"],
        config["base"]["subclip_end_seconds"],
    )
