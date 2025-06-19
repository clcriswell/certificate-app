import os
import json
import argparse
import sys
from PIL import Image, ImageOps
import pytesseract
import openai

SYSTEM_PROMPT = """You are an intelligent assistant built into the certificate generation app. A user uploads an event flyer or certificate request image. Your task is to analyze the image to extract all useful certificate fields, then reason about the event/requests's purpose and generate a commendation message accordingly.

Return the result strictly as JSON with keys: name, title, organization, date_raw, commendation, and an optional partners list if multiple logos or partners are identified."""


def ocr_image(path: str) -> str:
    """Return OCR text from the given image path."""
    img = ImageOps.exif_transpose(Image.open(path).convert("L"))
    return pytesseract.image_to_string(img)


def parse_certificate(text: str) -> dict:
    """Call the OpenAI API to parse certificate data from text."""
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
