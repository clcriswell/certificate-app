import os
import json
import argparse
import sys
from PIL import Image, ImageOps
import pytesseract
import openai

SYSTEM_PROMPT = """You are an intelligent assistant built into the certificate generation app. A user uploads an event flyer or certificate request image. Analyze the flyer text to identify only real, explicitly named individuals or organizations. Do not create placeholder names or titles. If a host or sponsoring organization is clearly listed, produce a certificate entry for that organization. Skip certificates for event themes or generic phrases and use patriotic or formal language in each commendation.

Return the result strictly as a JSON list of dictionaries. Each dictionary must contain: name, title, organization, date_raw, commendation. Include an optional partners list if multiple logos or partners are identified."""


def ocr_image(path: str) -> str:
    """Return OCR text from the given image path."""
    img = ImageOps.exif_transpose(Image.open(path).convert("L"))
    return pytesseract.image_to_string(img)


def parse_certificate(text: str) -> list:
    """Call the OpenAI API to parse certificate data from text and return a list of certificate dictionaries."""
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0,
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
