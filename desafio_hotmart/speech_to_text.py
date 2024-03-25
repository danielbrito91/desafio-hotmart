import json
import os

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


class ASR:
    """
    Automatic Speech Recognition (ASR) class.

    Args:
        model_id (str): The ID of the ASR model to use.
        audio_path (str): The path to the audio file to transcribe.
        output_path_with_ts (str): The path to save the transcription with timestamps in JSON format.
        output_path_text (str): The path to save the transcription in text format. Defaults to "data/output/transcricao.txt".
        language (str): The language of the audio file. Defaults to "portuguese".

    Methods:
        get_asr_pipeline: Returns the ASR pipeline.
        speech_to_text: Transcribes the audio file to text.
        export_transcription: Exports the transcription to JSON and text files.
        run: Runs the ASR process and returns the transcription.
    """

    def __init__(
        self,
        audio_path: str,
        output_path_with_ts: str,
        output_path_text: str,
        model_id: str = "openai/whisper-large-v3",
        language: str = "portuguese",
    ):
        if model_id != "openai/whisper-large-v3":
            raise ValueError("Only the 'openai/whisper-large-v3' model is supported.")

        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found at {audio_path}")

        self.model_id = model_id
        self.audio_path = audio_path
        self.output_path_ts = output_path_with_ts
        self.output_path_text = output_path_text
        self.language = language

    def get_asr_pipeline(self):
        """
        Returns the ASR pipeline.

        Returns:
            ASR pipeline: The pipeline for automatic speech recognition.
        """
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")

        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_id,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        )

        model.to(device)

        processor = AutoProcessor.from_pretrained(self.model_id)

        return pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            batch_size=16,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device,
        )

    def speech_to_text(self) -> dict:
        """
        Transcribes the audio file to text.

        Returns:
            dict: The transcription result with timestamps.
        """
        pipe = self.get_asr_pipeline()
        return pipe(self.audio_path, generate_kwargs={"language": self.language})

    def export_transcription(self, transcriptions: dict):
        """
        Exports the transcription to JSON and text files.

        Args:
            transcriptions (dict): The transcription result with timestamps.
        """
        output_dir = os.path.dirname(self.output_path_ts)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Write the dictionary to the JSON file
        with open(self.output_path_ts, "w") as file:
            json.dump(transcriptions, file)

        with open(self.output_path_text, "w") as file:
            file.write(transcriptions["text"])
