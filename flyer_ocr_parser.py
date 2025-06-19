import os
import json
import argparse
import sys
from PIL import Image, ImageOps
import pytesseract
import openai
import shutil

if shutil.which("tesseract") is None:
    raise RuntimeError(
        "Tesseract OCR is required but was not found in PATH. Install `tesseract-ocr`."
    )

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set. Provide your OpenAI API key to continue."
    )

SYSTEM_PROMPT = """You are an intelligent assistant built into the certificate generation app. A user uploads an event flyer or certificate request image. Analyze the flyer text to identify only real, explicitly named individuals or organizations. Do not create placeholder names or titles. If a host or sponsoring organization is clearly listed, produce a certificate entry for that organization. Skip certificates for event themes or generic phrases and use patriotic or formal language in each commendation.

Return the result strictly as a JSON list of dictionaries. Each dictionary must contain: name, title, organization, date_raw, commendation. Include an optional partners list if multiple logos or partners are identified."""


def ocr_image(path: str, conf_threshold: int = 10, line_gap: int = 25) -> str:
    """Return cleaned OCR text from the given image path.

    The function uses ``pytesseract.image_to_data`` to obtain layout
    information. Words with a confidence score below ``conf_threshold`` are
    discarded. Remaining words are grouped into lines if they are within
    ``line_gap`` pixels vertically and then sorted from left to right.
    """

    img = ImageOps.exif_transpose(Image.open(path).convert("L"))

    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    words = []
    for text, conf, left, top in zip(
        data["text"], data["conf"], data["left"], data["top"]
    ):
        text = text.strip()
        try:
            conf = int(conf)
        except ValueError:
            conf = 0
        if text and conf > conf_threshold:
            words.append({"text": text, "left": left, "top": top})

    if not words:
        return ""

    words.sort(key=lambda w: (w["top"], w["left"]))
    lines = []
    current_line = []
    current_top = words[0]["top"]

    for word in words:
        if abs(word["top"] - current_top) <= line_gap:
            current_line.append(word)
        else:
            lines.append(
                " ".join(w["text"] for w in sorted(current_line, key=lambda x: x["left"]))
            )
            current_line = [word]
            current_top = word["top"]

    if current_line:
        lines.append(
            " ".join(w["text"] for w in sorted(current_line, key=lambda x: x["left"]))
        )

    return "\n".join(lines)


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
