# Certificate Generator (Streamlit + GPT-4o)

This version uses `pdfminer.six` for stable PDF text extraction on Streamlit Cloud.

## 🚀 How to Deploy

1. Upload to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud) → New App
3. Choose `app.py` and connect your repo
4. In **Settings → Secrets**, add:
   ```
   OPENAI_API_KEY = "sk-..."
   ```
5. Done!
