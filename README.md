# LegAid – Certificate Generator

The certificate generator is now part of **LegAid**, a multi‑page Streamlit application.
It relies on `pdfminer.six` and `PyMuPDF` for PDF text extraction with Google Vision OCR as a fallback. In addition to text, Word, Excel and image uploads, the tool also accepts RTF documents and more image formats.
Uploaded images and scanned PDFs are processed through the Google Vision API so no system-level OCR installation is required. Generated certificates can be downloaded as Word documents or as PDFs.

## Prerequisites

Image uploads rely on these secrets:

- **google_vision_key** – add this key to your Streamlit secrets for OCR.
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

When the app generates the commendation text, the opening phrase after "On behalf of the California State Legislature"—such as "congratulations on," "honoring," or "celebrating"—is chosen automatically based on the certificate's category.

## ✨ Modify All

The **Modify All** box can modify any certificate field. For example:

- `Organization name for all certificates is "Acme Corp"` will set the organization on every certificate to "Acme Corp".
- `Use organization instead of title` copies the organization value into the Title field for each certificate.
- `Replace 'Officer' in title with organization` swaps the word "Officer" in every title with the certificate's organization.

After entering a comment, click **Recreate All Certificates** to apply the changes.

## 🏷️ Uniform Certificate Text

Enable the **Keep Certificate Text Uniformed** checkbox before generating certificates if you want identical language across every entry. The app will ask GPT to create a single certificate text template and automatically fill in each certificate's name, title, and organization.

## 🖼️ Parsing Event Flyers

Use `flyer_ocr_parser.py` to extract certificate fields directly from an event flyer or request image. Provide the path to the image along with the `OPENAI_API_KEY` and `GOOGLE_VISION_KEY` environment variables:

```bash
python flyer_ocr_parser.py path/to/flyer.png
```

The script performs OCR on the image, sends the text to GPT for analysis, and prints a JSON **list** of dictionaries with the extracted name, title, organization, date, commendation, and any partners found. Only real individuals or organizations will be returned.

## 🗣️ Speech Creator

Craft speeches with a personalized voice profile. The page reads sample text you upload, builds a profile, and generates a draft speech based on details you provide.

### Required Secrets

- **OPENAI_API_KEY** – used for generating drafts.
- **GITHUB_TOKEN** – enables saving profiles and speeches back to the repo.

Launch the page with:

```bash
streamlit run SpeechCreate.py
```

After generating a draft you can download the speech and bullet‑point notes or push the files to GitHub.
