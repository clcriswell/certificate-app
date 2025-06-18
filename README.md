# Certificate Generator (Streamlit + GPT-4o)

This version uses `pdfminer.six` for stable PDF text extraction on Streamlit Cloud.
You can also upload text, Word, Excel, CSV, and image files. Images are processed using OCR via Tesseract (make sure the `tesseract` binary is installed).

## 🚀 How to Deploy

1. Upload to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud) → New App
3. Choose `app.py` and connect your repo
4. In **Settings → Secrets**, add:
   ```
   OPENAI_API_KEY = "sk-..."
   ```
5. Done!

## 📝 Certificate Extraction Guidelines

When extracting certificate information, the app uses GPT to parse titles and organizations from event text. If an organization is hosting the event, its name should **not** be placed in the Title block for certificates associated with the host. Only include "Title of Organization" when an individual or group from that organization is being recognized by the host organization.

## ✨ Global Comments

The **Global Comments** box can modify any certificate field. For example:

- `Organization name for all certificates is "Acme Corp"` will set the organization on every certificate to "Acme Corp".
- `Use organization instead of title` copies the organization value into the Title field for each certificate.
- `Replace 'Officer' in title with organization` swaps the word "Officer" in every title with the certificate's organization.

After entering a global comment, click **Regenerate All Certificates** to apply the changes.

## 🏷️ Uniform Commendation by Category

Before generating certificates you can enable **Use uniform commendation per category**. When selected, the app asks GPT to produce one sample commendation for each category and applies it to every certificate in that group. You can adjust the text in the provided boxes and click **Apply Uniform Commendations** to update all certificates at once.
