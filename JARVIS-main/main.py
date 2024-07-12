import os
from os import PathLike
from time import time
import asyncio
from typing import Union

from dotenv import load_dotenv
from deepgram import Deepgram
import pygame
from pygame import mixer
from gtts import gTTS  # Import the gTTS library

from record import speech_to_text

# Load API keys
load_dotenv()
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Initialize APIs
from google.generativeai import configure, GenerativeModel
configure(api_key=GOOGLE_API_KEY)
model = GenerativeModel('gemini-1.5-flash')
deepgram = Deepgram(DEEPGRAM_API_KEY)
mixer.init()

# Change the prompt if you want to change Jarvis' personality
prompt = "You are Jarvis, Boss human assistant. You are witty and full of personality. Your answers should be limited to 1-2 short sentences."
conversation = {"Conversation": []}
RECORDING_PATH = "audio/recording.wav"


def request_gemini(prompt: str) -> str:
    """Generate content using the Gemini model"""
    response = model.generate_content(prompt)
    return response.text


async def transcribe(file_name: Union[Union[str, bytes, PathLike[str], PathLike[bytes]], int]):
    """Transcribe audio using Deepgram API"""
    with open(file_name, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/wav"}
        response = await deepgram.transcription.prerecorded(source)
        return response["results"]["channels"][0]["alternatives"][0]["words"]

def log(log: str):
    """
    Print and write to status.txt
    """
    print(log)
    with open("status.txt", "w") as f:
        f.write(log)


if __name__ == "__main__":
    while True:
        # Record audio
        log("Listening...")
        speech_to_text()
        log("Done listening")

        # Transcribe audio
        current_time = time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        words = loop.run_until_complete(transcribe(RECORDING_PATH))
        string_words = " ".join(
            word_dict.get("word") for word_dict in words if "word" in word_dict
        )
        with open("conv.txt", "a") as f:
            f.write(f"{string_words}\n")
        transcription_time = time() - current_time
        log(f"Finished transcribing in {transcription_time:.2f} seconds.")

        # Get response from GPT-3
        current_time = time()
        prompt += f"\nArasu: {string_words}\nJarvis: "
        response = request_gemini(prompt)
        prompt += response
        gpt_time = time() - current_time
        log(f"Finished generating response in {gpt_time:.2f} seconds.")

        # Convert response to audio using gTTS
        current_time = time()
        tts = gTTS(response)
        tts.save("audio/response.mp3")
        audio_time = time() - current_time
        log(f"Finished generating audio in {audio_time:.2f} seconds.")

        # Play response
        log("Speaking...")
        sound = mixer.Sound("audio/response.mp3")
        # Add response as a new line to conv.txt
        with open("conv.txt", "a", encoding='utf-8') as f:
            f.write(f"{response}\n")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))
        print(f"\n --- USER: {string_words}\n --- JARVIS: {response}\n")