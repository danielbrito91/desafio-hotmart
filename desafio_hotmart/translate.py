import json
import os
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from transformers import pipeline


class Translator:
    """
    A class that provides translation functionality using different translation models.

    Args:
        data_with_timestamps_path (str): The path to the file containing data with timestamps.
        translator (Literal["nllb", "openai"]): The translator to use. Must be either "nllb" or "openai".
        output_path_json (str): The path to save the translated data in JSON format with the timestamps.
        output_path_txt (str): The path to save the translated data in text format.

    Attributes:
        translator (str): The translator being used.
        openai_client (OpenAI): The OpenAI client for translation.
        data_with_timesamps (dict): The data with timestamps loaded from the file.

    Methods:
        translate_with_nllb: Translates text using the NLLB translation model.
        translate_with_openai: Translates text using the OpenAI translation model.
        translate_chunks: Translates chunks of text using the selected translator.

    Returns:
        dict: The translated data.

    Raises:
        ValueError: If an invalid translator is provided.
    """

    def __init__(
        self,
        data_with_timestamps_path: str,
        translator: Literal["nllb", "openai"],
        output_path_json: str,
        output_path_txt: str,
    ):
        load_dotenv()

        self.translator = translator
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.output_path_json = output_path_json
        self.output_path_txt = output_path_txt

        with open(data_with_timestamps_path, "r") as f:
            self.data_with_timesamps = json.load(f)

    def translate_with_nllb(
        self,
        src_text: str,
        model: str = "facebook/nllb-200-distilled-600M",
        src_lang: str = "por_Latn",
        tgt_lang: str = "eng_Latn",
    ) -> str:
        """
        Translates text using the NLLB translation model.

        Args:
            src_text (str): The source text to be translated.
            model (str, optional): The NLLB translation model to use. Defaults to "facebook/nllb-200-distilled-600M".
            src_lang (str, optional): The source language. Defaults to "por_Latn".
            tgt_lang (str, optional): The target language. Defaults to "eng_Latn".

        Returns:
            str: The translated text.
        """
        translator = pipeline(
            "translation", model=model, tgt_lang=tgt_lang, src_lang=src_lang
        )
        return translator(src_text)[0]["translation_text"]

    def translate_with_openai(
        self,
        src_text: str,
        model: str = "gpt-3.5-turbo",
        system_prompt: str = """
Translate this Portuguese sentence into English.
Please, do not translate names, brands (such as 'Salude') and places, keeping them in the translated text.
Do not insert any new information.
If you see the isolated word 'Beleza?', consider translating it as 'Okay?' or 'Alright?'.
Try to keep the same tone and style of the original text, and also the same length, considering that the translation will be used in a voice-over.""",
        temperature: float = 0.2,
    ) -> str:
        """
        Translates text using the OpenAI translation model.

        Args:
            src_text (str): The source text to be translated.
            model (str, optional): The OpenAI translation model to use. Defaults to "gpt-3.5-turbo".
            system_prompt (str, optional): The system prompt for the translation. Defaults to the system prompt provided.
            temperature (float, optional): The temperature for the translation. Defaults to 0.2.

        Returns:
            str: The translated text.
        """
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": src_text},
            ],
            temperature=temperature,
        )

        return response.model_dump()["choices"][0]["message"]["content"]

    def translate_chunks(self) -> dict:
        """
        Translates chunks of text using the selected translator.

        Returns:
            dict: The translated data.
        """
        translated_chunks = []
        for chunk in self.data_with_timesamps["chunks"]:
            text = chunk["text"]

            if self.translator == "nllb":
                translated_text = self.translate_with_nllb(text)
            elif self.translator == "openai":
                translated_text = self.translate_with_openai(text)
            else:
                raise ValueError(
                    "Invalid translator. Please choose either 'nllb' or 'openai'."
                )

            translated_chunk = dict(timestamp=chunk["timestamp"], text=translated_text)
            translated_chunks.append(translated_chunk)

        concatenated_text = ""

        for chunk in translated_chunks:
            concatenated_text += chunk["text"] + " "

        translated_data = dict(
            complete_text=None,
            concat_text=concatenated_text,
            chunks=translated_chunks,
        )

        return translated_data

    def export_translation(self, translated_data: dict) -> None:
        """
        Exports the translation to a JSON and txt file.

        Args:
            translated_data (dict): The translated data.
        """
        with open(self.output_path_json, "w") as f:
            json.dump(translated_data, f, indent=4)

        with open(self.output_path_txt, "w") as f:
            f.write(translated_data["concat_text"])
