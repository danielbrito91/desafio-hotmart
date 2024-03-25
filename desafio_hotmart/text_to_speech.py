import json
import os
from typing import Literal

from gtts import gTTS
from pydub import AudioSegment
from TTS.api import TTS


class TextToSpeech:
    """
    A class that converts text to speech using either Google Text-to-Speech or Coqui TTS.

    Args:
        text_path_with_timestamps (str): The path to the text file with timestamps.
        audio_output_path (str): The path to save the generated audio file.
        voice (Literal["google", "coqui"]): The voice to use for text-to-speech conversion.
        speaker_audio_path (str): The path to the speaker audio file that will be used by Coqui TTS.
        min_speed_allowed (float, optional): The minimum allowed speed for speech. Defaults to 1.
        max_speed_allowed (float, optional): The maximum allowed speed for speech. Defaults to 1.25.
        language (str, optional): The language of the text. Defaults to "en".
        add_time (float, optional): The time to add to the start of the next chunk when it returns to zero. Defaults to 29.
        chunk_index_to_adjust_speed (list, optional): The indexes of the chunks to adjust the speed manually. Defaults to [37, 47].

    Raises:
        FileNotFoundError: If the speaker audio file, or text file is not found.
        ValueError: If the speaker audio file is not in .mp3 or .wav format.

    Attributes:
        complete_text (dict): The complete text with timestamps.
        audio_output_path (str): The path to save the generated audio file.
        voice (Literal["google", "coqui"]): The voice to use for text-to-speech conversion.
        speaker_audio_path (str): The path to the speaker audio file.
        min_speed_allowed (float): The minimum allowed speed for speech.
        max_speed_allowed (float): The maximum allowed speed for speech.
        language (str): The language of the text.
        add_time (float): The time to add to the start of the next chunk when it returns to zero.
        chunk_index_to_adjust_speed (list): The indexes of the chunks to adjust the speed manually.

    Methods:
        get_chunk_durations_in_seconds(i: int) -> Tuple[float, float]:
            Get the durations of the current chunk in seconds (complete chunk (speech + silence), and speech).

        set_speed(speed_max: float, speed_min: float) -> float:
            Set the speed for a given chunk based on the durations of the TTS audio and the original audio.

        speed_up(speed: float, seg: AudioSegment, source_total_duration: float) -> AudioSegment:
            Speed up the audio segment to the given speed, filling the remaining time with silence.

        _get_audio_path(i: int) -> str:
            Get the path to the audio file for the given chunk index.

        speech_to_text_with_coqui(text: str, i: int, model: str = "tts_models/multilingual/multi-dataset/xtts_v2") -> None:
            Convert text to speech using Coqui TTS.

        speech_to_text_with_google(text: str, i: int) -> None:
            Convert text to speech using Google Text-to-Speech.

        convert_chunks_to_speech() -> AudioSegment:
            Convert the text chunks to speech and return the final audio.

        export_audio(final_audio: AudioSegment, remove_temp_files: bool = True) -> None:
            Export the final audio to the specified audio output path.
    """

    def __init__(
        self,
        text_path_with_timestamps: str,
        audio_output_path: str,
        voice: Literal["google", "coqui"],
        speaker_audio_path: str,
        min_speed_allowed: float = 1,
        max_speed_allowed: float = 1.25,
        language: str = "en",
        add_time: float = 29,
        chunk_index_to_adjust_speed: list = [37, 47],
    ):
        with open(text_path_with_timestamps, "r") as f:
            self.complete_text = json.load(f)

        # Exporta o áudio do speaker para .wav, caso esteja em .mp3
        if speaker_audio_path.split(".")[-1] == "mp3":
            sound = AudioSegment.from_mp3(speaker_audio_path)
            speaker_audio_path = speaker_audio_path.replace(".mp3", ".wav")
            sound.export(speaker_audio_path, format="wav")
            self.speaker_audio_path = speaker_audio_path
        elif speaker_audio_path.split(".")[-1] == "wav":
            self.speaker_audio_path = speaker_audio_path
        else:
            raise ValueError("Speaker audio file must be in .mp3 or .wav format")

        self.audio_output_path = audio_output_path
        self.voice = voice
        self.speaker_audio_path = speaker_audio_path
        self.max_speed_allowed = max_speed_allowed
        self.min_speed_allowed = min_speed_allowed
        self.language = language
        self.add_time = add_time
        self.chunk_index_to_adjust_speed = chunk_index_to_adjust_speed

        if not os.path.isfile(self.speaker_audio_path):
            raise FileNotFoundError(
                f"Speaker audio file not found at {self.speaker_audio_path}"
            )
        if not os.path.isfile(text_path_with_timestamps):
            raise FileNotFoundError(
                f"Text file not found at {text_path_with_timestamps}"
            )
        if self.voice == "coqui":
            os.environ["COQUI_TOS_AGREED"] = "1"

    def get_chunk_durations_in_seconds(self, i: int):
        """
        Get the durations of the current chunk in seconds.

        Args:
            i (int): The index of the current chunk.

        Returns:
            Tuple[float, float]: The complete duration (speech + silence) and the speech duration of the chunk.
        """
        is_last_chunck = i == (len(self.complete_text["chunks"]) - 1)
        if is_last_chunck:
            current_chunk_ts = self.complete_text["chunks"][i]["timestamp"]

            current_chunk_complete_duration = current_chunk_ts[1] - current_chunk_ts[0]
            silence_duration = 0
            current_chunk_speech_duration = current_chunk_complete_duration

        else:
            current_chunk_ts = self.complete_text["chunks"][i]["timestamp"]
            next_chunk_ts = self.complete_text["chunks"][i + 1]["timestamp"]

            if next_chunk_ts[0] < current_chunk_ts[1]:
                # if next_chunk_ts[0] > 0:
                #     # alguns chunks começam com um pequeno atraso, então é necessário ajustar o tempo
                #     next_chunk_ts = [ts + (self.add_time  - next_chunk_ts[0]) for ts in next_chunk_ts]
                # else:
                # if current_chunk_ts[1] == self.add_time:
                #     add_time = self.add_time + 1
                # else:
                #     add_time = self.add_time
                next_chunk_ts = [ts + self.add_time for ts in next_chunk_ts]

            current_chunk_complete_duration = next_chunk_ts[0] - current_chunk_ts[0]
            silence_duration = next_chunk_ts[0] - current_chunk_ts[1]
            current_chunk_speech_duration = current_chunk_ts[1] - current_chunk_ts[0]

        assert current_chunk_complete_duration == (
            silence_duration + current_chunk_speech_duration
        )

        return (
            current_chunk_complete_duration,
            current_chunk_speech_duration,
        )

    def set_speed(
        self,
        tts_duration: float,
        source_speech_duration: float,
        source_total_duration: float,
    ):
        """
        Set the speed for a given chunk based on the durations of the TTS audio and the original audio.

        Args:
            tts_duration (float): The duration of the TTS audio of the current chunk.
            source_speech_duration (float): The duration of the speech in the original audio of the current chunk.
            source_total_duration (float): The total duration of the original audio of the current chunk (speech + silence).

        Returns:
            float: The selected speed.
        """
        speed_max = tts_duration / source_speech_duration
        speed_min = tts_duration / source_total_duration

        if (speed_max >= self.max_speed_allowed) & (
            speed_min >= self.min_speed_allowed
        ):
            speed = speed_min
        elif (speed_max >= self.max_speed_allowed) & (
            speed_min < self.min_speed_allowed
        ):
            speed = self.min_speed_allowed
        elif (speed_max < self.max_speed_allowed) & (
            speed_max >= self.min_speed_allowed
        ):
            speed = speed_max
        elif speed_max < self.min_speed_allowed:
            speed = self.min_speed_allowed

        return speed

    def speed_up(self, speed: float, seg: AudioSegment, source_total_duration: float):
        """
        Speed up the audio segment to the given speed, filling the remaining time with silence.

        Args:
            speed (float): The speed to accelerate the audio segment to.
            seg (AudioSegment): The audio segment to accelerate.
            source_total_duration (float): The total duration of the original audio of the current chunk (speech + silence).

        Returns:
            AudioSegment: The accelerated audio segment.
        """
        if speed > 1:
            seg_speed = seg.speedup(playback_speed=speed)
        else:
            # Quando se inseria speed = 1 (menor valor permitido), verificava-se que o áudio perdia qualidade
            # Assim, optou-se por manter o áudio original, sem aceleração (ocupando parte do silêncio do trecho original)
            seg_speed = seg

        silence_duration = source_total_duration - seg_speed.duration_seconds

        if silence_duration > 0:
            seg_speed += AudioSegment.silent(
                silence_duration * 1000, seg_speed.frame_rate
            )

        return seg_speed

    def _get_audio_path(self, i: int) -> str:
        """
        Get the path to the audio file for the given chunk index.

        Args:
            i (int): The index of the current chunk.

        Returns:
            str: The path to the audio file.
        """
        audio_path = f"data/audio_segments/{i}.wav"
        audio_dir = os.path.dirname(audio_path)
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)

        return audio_path

    def speech_to_text_with_coqui(
        self,
        text: str,
        i: int,
        model: str = "tts_models/multilingual/multi-dataset/xtts_v2",
    ) -> None:
        """
        Convert text to speech using Coqui TTS.

        Args:
            text (str): The text to convert to speech.
            i (int): The index of the current chunk.
            model (str, optional): The path to the Coqui TTS model. Defaults to "tts_models/multilingual/multi-dataset/xtts_v2".
        """
        tts = TTS(model, gpu=False)

        audio_path = self._get_audio_path(i)

        tts.tts_to_file(
            text=text,
            file_path=audio_path,
            speaker_wav=self.speaker_audio_path,
            language=self.language,
        )

    def speech_to_text_with_google(self, text: str, i: int) -> None:
        """
        Convert text to speech using Google Text-to-Speech.

        Args:
            text (str): The text to convert to speech.
            i (int): The index of the current chunk.
        """
        audio = gTTS(text, lang=self.language)
        audio_path = self._get_audio_path(i)
        audio.save(audio_path)

    def convert_chunks_to_speech(self) -> AudioSegment:
        """
        Convert the text chunks to speech and return the final audio.

        Returns:
            AudioSegment: The final audio segment.
        """
        final_audio = AudioSegment.empty()

        for i in range(len(self.complete_text["chunks"])):

            source_total_duration, source_speech_duration = (
                self.get_chunk_durations_in_seconds(i)
            )

            if not os.path.exists(self._get_audio_path(i)):
                if self.voice == "google":
                    self.speech_to_text_with_google(
                        text=self.complete_text["chunks"][i]["text"], i=i
                    )

                elif self.voice == "coqui":
                    self.speech_to_text_with_coqui(
                        text=self.complete_text["chunks"][i]["text"], i=i
                    )

            seg = AudioSegment.from_file(self._get_audio_path(i))
            tts_duration = seg.duration_seconds

            # Quando "sobra" tempo na fala do TTS, preenche-se com silêncio
            if tts_duration <= source_speech_duration:
                delta_time = tts_duration - source_speech_duration
                seg_speed = seg + AudioSegment.silent(delta_time * 1000, seg.frame_rate)

            # Quando fala TTS é mais longa que a fala observada no áudio originak, necessidade de acelerar conforme lógica de velocidades (`self.set_speed`)
            # permitindo-se ocupar parte do silêncio do trecho original (em português) com a fala traduzida (em inglês)

            elif tts_duration > source_speech_duration:
                if i in self.chunk_index_to_adjust_speed:
                    # Trechos que ficaram muito acelerados, então foi necessário ajustar manualmente
                    speed = self.max_speed_allowed
                else:
                    speed = self.set_speed(
                        tts_duration, source_speech_duration, source_total_duration
                    )
                seg_speed = self.speed_up(speed, seg, source_total_duration)

            final_audio += seg_speed

        return final_audio

    def export_audio(
        self, final_audio: AudioSegment, remove_temp_files: bool = True
    ) -> None:
        """
        Export the final audio to the specified audio output path.

        Args:
            final_audio (AudioSegment): The final audio segment.
        """
        final_audio.export(self.audio_output_path, format="wav")

        # Remove the audio files and the folder "data/audio_segments"
        if remove_temp_files:
            for i in range(len(self.complete_text["chunks"])):
                audio_path = self._get_audio_path(i)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            if os.path.exists("data/audio_segments"):
                os.rmdir("data/audio_segments")
