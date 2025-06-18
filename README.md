# LegAid – Certificate Generator

The certificate generator is now part of **LegAid**, a multi‑page Streamlit application.
It still relies on `pdfminer.six` for stable PDF text extraction and supports text, Word, Excel,
CSV and image uploads. Images are processed using OCR via Tesseract (ensure the
`tesseract` binary is installed).
Generated certificates can be downloaded as Word documents or as PDFs.

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

## ✨ Edit All

The **Edit All** box can modify any certificate field. For example:

- `Organization name for all certificates is "Acme Corp"` will set the organization on every certificate to "Acme Corp".
- `Use organization instead of title` copies the organization value into the Title field for each certificate.
- `Replace 'Officer' in title with organization` swaps the word "Officer" in every title with the certificate's organization.

After entering a comment, click **Regenerate All Certificates** to apply the changes.

## 🏷️ Uniform Certificate Text

Enable the **Keep Certificate Text Uniformed** checkbox before generating certificates if you want identical language across every entry. The app will ask GPT to create a single certificate text template and automatically fill in each certificate's name, title, and organization.
