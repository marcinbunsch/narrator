import os
from openai import OpenAI
import base64
import json
import time
import simpleaudio as sa
import errno
from elevenlabs import generate, play, set_api_key, voices, Voice
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

set_api_key(os.environ.get("ELEVENLABS_API_KEY"))

def encode_image(image_path):
    while True:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except IOError as e:
            if e.errno != errno.EACCES:
                # Not a "file in use" error, re-raise
                raise
            # File is being written to, wait a bit and retry
            time.sleep(0.1)


def play_audio(text):
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
    audio = generate(text, voice=Voice(voice_id=voice_id), model="eleven_multilingual_v2")

    unique_id = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8").rstrip("=")
    dir_path = os.path.join("narration", unique_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, "audio.wav")

    with open(file_path, "wb") as f:
        f.write(audio)

    play(audio)


def generate_new_line(base64_image):
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Opisz to zdjęcie"},
                {
                    "type": "image_url",
                    "image_url": {"url":f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        },
    ]


def analyze_image(base64_image, script):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                Odgrywasz rolę Krystyny Czubówny. Opisz zdjęcie w stylu dokumentu przyrodniczego. 
                Bądź ironiczna i zabawna. Nie powtarzaj się. Bądź zwięzła, maksimum 3 zdania. 
                """,
            },
        ]
        + script
        + generate_new_line(base64_image),
        max_tokens=500,
    )
    response_text = response.choices[0].message.content
    return response_text


def main():
    script = []

    while True:
        # path to your image
        image_path = os.path.join(os.getcwd(), "./frames/frame.jpg")

        # getting the base64 encoding
        base64_image = encode_image(image_path)

        # analyze posture
        print("👀 Krystyna ogląda...")
        analysis = analyze_image(base64_image, script=script)

        print("🎙️ Krystyna:")
        print(analysis)

        play_audio(analysis)

        script = script + [{"role": "assistant", "content": analysis}]

        # wait for 5 seconds
        time.sleep(5)


if __name__ == "__main__":
    main()
