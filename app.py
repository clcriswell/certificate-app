import streamlit as st
import re, os, json, tempfile
from datetime import datetime
import pandas as pd
from pdfminer.high_level import extract_text
import openai
from io import StringIO

# ─── CONFIG ─────────────────────────────────────────────
openai.api_key = st.secrets["OPENAI_API_KEY"]
OPENAI_MODEL = "gpt-4o"

def format_certificate_date(raw_date_str):
    try:
        dt = datetime.strptime(raw_date_str, "%B %d, %Y")
    except ValueError:
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(raw_date_str, fmt)
                break
            except ValueError:
                continue
        else:
            return "Dated ______"
    day = dt.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    month = dt.strftime("%B")
    year_words = {
        "2025": "Two Thousand and Twenty-Five",
        "2024": "Two Thousand and Twenty-Four",
        "2023": "Two Thousand and Twenty-Three"
    }.get(dt.strftime("%Y"), dt.strftime("%Y"))
    return f"Dated the {day}{suffix} of {month}\n{year_words}"

def fallback_commendation(name, title, org):
    title_lower = title.lower()
    if "award" in title_lower or "of the year" in title_lower or "honoree" in title_lower:
        msg = f"On behalf of the California State Legislature, congratulations on being recognized as {org}'s {title}. "
    elif any(kw in title_lower for kw in ["president", "officer", "board", "service", "chair", "director"]):
        msg = f"On behalf of the California State Legislature, thank you for your service as {title} with {org}. "
    elif "opening" in title_lower or "grand" in title_lower:
        msg = f"On behalf of the California State Legislature, congratulations on the opening of {org}. "
    elif "graduat" in title_lower:
        msg = f"On behalf of the California State Legislature, congratulations on successfully graduating from {org}. "
    else:
        msg = f"On behalf of the California State Legislature, we commend you for your accomplishments with {org}. "
    msg += "This recognition speaks highly of your dedication and contributions to the community."
    return msg

def categorize_tone(title):
    title_lower = title.lower()
    if any(kw in title_lower for kw in ["award", "of the year", "honoree", "achievement", "excellence", "inductee"]):
        return "🏆 Award"
    elif any(kw in title_lower for kw in ["president", "officer", "board", "service", "chair", "director"]):
        return "👥 Service"
    elif any(kw in title_lower for kw in ["opening", "grand", "event", "dedication", "launch"]):
        return "🏛 Event"
    elif any(kw in title_lower for kw in ["graduate", "class of", "commencement"]):
        return "🎓 Graduation"
    else:
        return "📝 Recognition"

# ─── UI SETUP ───────────────────────────────────────────
st.set_page_config(layout="centered")
st.title("📑 Certificate CSV Generator (Multi-Entry)")
st.markdown("Upload a PDF certificate request and preview all auto-extracted entries before downloading a CSV.")

pdf_file = st.file_uploader("📎 Upload Certificate Request PDF", type=["pdf"])
if not pdf_file:
    st.stop()

# ─── TEXT EXTRACTION ───────────────────────────────────
with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
    tmp.write(pdf_file.read())
    tmp_path = tmp.name
pdf_text = extract_text(tmp_path)
os.remove(tmp_path)

# ─── GPT EXTRACTION ─────────────────────────────────────
st.info("⏳ Detecting multiple certificate entries using GPT...")

SYSTEM_PROMPT = """
You will be given the full text of a certificate request. Your job is to extract ALL the individual certificates mentioned.

For each one, return:
- name
- title (award or position)
- organization
- date_raw (the event date if provided, otherwise 'unknown')
- commendation: A 1–2 sentence formal message starting with "On behalf of the California State Legislature, ..."

Return ONLY a valid JSON array of objects. No commentary, no markdown, no explanations.
"""

cert_rows = []

try:
    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pdf_text}
        ],
        temperature=0
    )
    content = response["choices"][0]["message"]["content"].strip().strip("```json").strip("```")
    parsed_entries = json.loads(content)

    for parsed in parsed_entries:
        cert_rows.append({
            "Name": parsed["name"],
            "Title": parsed["title"],
            "Organization": parsed["organization"],
            "Certificate_Text": parsed["commendation"],
            "Formatted_Date": format_certificate_date(parsed["date_raw"]),
            "Tone_Category": categorize_tone(parsed["title"])
        })

except Exception as e:
    st.error("⚠️ GPT failed to extract entries. Adding a fallback row.")
    cert_rows.append({
        "Name": "UNKNOWN",
        "Title": "UNKNOWN",
        "Organization": "UNKNOWN",
        "Certificate_Text": fallback_commendation("UNKNOWN", "UNKNOWN", "UNKNOWN"),
        "Formatted_Date": "Dated ______",
        "Tone_Category": "📝 Recognition"
    })

# ─── PREVIEW ────────────────────────────────────────────
st.subheader("👁 Preview Extracted Certificates")
for i, cert in enumerate(cert_rows, 1):
    with st.expander(f"{cert['Tone_Category']} #{i}: {cert['Name']} – {cert['Title']}"):
        st.write(f"**Organization:** {cert['Organization']}")
        st.write(f"**Date:** {cert['Formatted_Date']}")
        st.text_area("📜 Commendation", cert["Certificate_Text"], height=100)

# ─── EXPORT TO CSV ──────────────────────────────────────
if st.button("📥 Download CSV for Mail Merge"):
    df = pd.DataFrame(cert_rows)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    st.download_button(
        label="📊 Download CSV",
        data=csv_data,
        file_name="Certificates_MailMerge.csv",
        mime="text/csv"
    )
