# LegAid – Certificate Generator

The certificate generator is now part of **LegAid**, a multi‑page Streamlit application.
It relies on `pdfminer.six` and `PyMuPDF` for PDF text extraction with an OCR fallback using Tesseract when needed. In addition to text, Word, Excel and image uploads, the tool also accepts RTF documents and more image formats.
Uploaded images and scanned PDFs are processed with Tesseract OCR (ensure the `tesseract` binary is installed). Generated certificates can be downloaded as Word documents or as PDFs.

## Prerequisites

Image uploads rely on external tools:

- **Tesseract OCR** – install the `tesseract` executable and make sure it is in your PATH. On Ubuntu/Debian you can install it with:

  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr
  ```

- **OPENAI_API_KEY** – set this environment variable with your OpenAI API key so the app can parse text.

Run the entire suite with:

```bash
streamlit run LegAid/app.py
```

## 🚀 How to Deploy

1. Upload to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud) → New App
3. Choose `LegAid/app.py` and connect your repo
4. In **Settings → Secrets**, add:
   ```
   OPENAI_API_KEY = "sk-..."
   ```
5. Done! Launch the app and select **Certificate Generator** from the sidebar.

## 📝 Certificate Extraction Guidelines

When extracting certificate information, the app uses GPT to parse titles and organizations from event text. If an organization is hosting the event, its name should **not** be placed in the Title block for certificates associated with the host. Only include "Title of Organization" when an individual or group from that organization is being recognized by the host organization.

If some details are missing from the text, the generator will now produce partial certificates with any fields it can infer. Blank values can be edited later in the interface.

## ✨ Modify All

The **Modify All** box can modify any certificate field. For example:

- `Organization name for all certificates is "Acme Corp"` will set the organization on every certificate to "Acme Corp".
- `Use organization instead of title` copies the organization value into the Title field for each certificate.
- `Replace 'Officer' in title with organization` swaps the word "Officer" in every title with the certificate's organization.

After entering a comment, click **Recreate All Certificates** to apply the changes.

## 🏷️ Uniform Certificate Text

Enable the **Keep Certificate Text Uniformed** checkbox before generating certificates if you want identical language across every entry. The app will ask GPT to create a single certificate text template and automatically fill in each certificate's name, title, and organization.

## 🖼️ Parsing Event Flyers

Use `flyer_ocr_parser.py` to extract certificate fields directly from an event flyer or request image. Provide the path to the image and ensure `tesseract` is installed and the `OPENAI_API_KEY` environment variable is set:

```bash
python flyer_ocr_parser.py path/to/flyer.png
```

The script performs OCR on the image, sends the text to GPT for analysis, and prints a JSON **list** of dictionaries with the extracted name, title, organization, date, commendation, and any partners found. Only real individuals or organizations will be returned.
