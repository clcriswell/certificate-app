import os
import json
import argparse
import sys
from PIL import Image, ImageOps
from io import BytesIO
import base64
import requests
import openai

from LegAid.utils.shared_functions import normalize_date_strings


if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set. Provide your OpenAI API key to continue."
    )

if not os.getenv("GOOGLE_VISION_KEY"):
    raise RuntimeError(
        "GOOGLE_VISION_KEY environment variable is not set. Provide your Google Vision API key to continue."
    )

SYSTEM_PROMPT = """You are an intelligent assistant built into the certificate generation app. A user uploads an event flyer or certificate request image. Analyze the flyer text to identify only real, explicitly named individuals or organizations. Do not create placeholder names or titles. If a host or sponsoring organization is clearly listed, produce a certificate entry for that organization. Skip certificates for event themes or generic phrases and use patriotic or formal language in each commendation.

Return the result strictly as a JSON list of dictionaries. Each dictionary must contain: name, title, organization, date_raw, commendation. Include an optional partners list if multiple logos or partners are identified."""


def ocr_image(path: str) -> str:
    """Return OCR text from the given image path using Google Vision API."""

    key = os.getenv("GOOGLE_VISION_KEY")
    if not key:
        raise RuntimeError("GOOGLE_VISION_KEY environment variable is not set.")

    img = ImageOps.exif_transpose(Image.open(path))
    buf = BytesIO()
    img.save(buf, format="PNG")

    payload = {
        "requests": [
            {
                "image": {"content": base64.b64encode(buf.getvalue()).decode()},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            }
        ]
    }

    resp = requests.post(
        "https://vision.googleapis.com/v1/images:annotate",
        params={"key": key},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["responses"][0].get("fullTextAnnotation", {}).get("text", "")


def parse_certificate(text: str) -> list:
    """Call the OpenAI API to parse certificate data from text and return a list of certificate dictionaries."""

    text = normalize_date_strings(text)
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0,
        max_tokens=2000,
    )
    content = response.choices[0].message.content
    cleaned = content.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(cleaned)


def main():
    parser = argparse.ArgumentParser(description="Extract certificate data from an image flyer.")
    parser.add_argument("image", help="Path to the image file")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        raise FileNotFoundError(args.image)

    text = ocr_image(args.image)
    data = parse_certificate(text)
    json.dump(data, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
