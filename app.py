import streamlit as st
import re, os, json, tempfile, io, requests
from datetime import datetime
import pandas as pd
from pdfminer.high_level import extract_text
import openai
from docx import Document
from copy import deepcopy

# ─── CONFIG ─────────────────────────────────────────────
openai.api_key = st.secrets["OPENAI_API_KEY"]
OPENAI_MODEL = "gpt-4o"
GITHUB_TEMPLATE_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/YOUR_TEMPLATE.docx"  # CHANGE THIS

# ─── HELPERS ────────────────────────────────────────────
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
        return "\U0001F3C6 Award"
    elif any(kw in title_lower for kw in ["president", "officer", "board", "service", "chair", "director"]):
        return "\U0001F46E Service"
    elif any(kw in title_lower for kw in ["opening", "grand", "event", "dedication", "launch"]):
        return "\U0001F3DB Event"
    elif any(kw in title_lower for kw in ["graduate", "class of", "commencement"]):
        return "\U0001F393 Graduation"
    else:
        return "\U0001F4DD Recognition"

def extract_event_date(text):
    match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2},\\s+20\\d{2}", text)
    if match:
        return match.group(0)
    match = re.search(r"\\d{1,2}/\\d{1,2}/20\\d{2}", text)
    if match:
        return match.group(0)
    return "unknown"

def load_template_from_github(url):
    response = requests.get(url)
    if response.status_code == 200:
        return io.BytesIO(response.content)
    else:
        st.error("❌ Failed to load Word template from GitHub.")
        return None

# ─── UI SETUP ───────────────────────────────────────────
st.set_page_config(layout="centered")
st.title("📑 Certificate CSV Generator + Word Merge")
st.markdown("Upload a PDF certificate request and preview all auto-extracted entries before downloading a CSV or Word file.")

pdf_file = st.file_uploader("📎 Upload Certificate Request PDF", type=["pdf"])
if not pdf_file:
    st.stop()

with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
    tmp.write(pdf_file.read())
    tmp_path = tmp.name
pdf_text = extract_text(tmp_path)
os.remove(tmp_path)

event_date = extract_event_date(pdf_text)

st.info(f"⏳ Detecting multiple certificate entries using GPT...\n📅 Event date detected: {event_date}")

SYSTEM_PROMPT = f"""
You will be given the full text of a certificate request. Your job is to extract ALL the individual certificates mentioned.

The event date for this request is: {event_date}

For each certificate, return:
- name
- title (award or position)
- organization
- date_raw (use the event date if no specific date is mentioned per recipient)
- commendation: A 1–2 sentence formal message starting with \"On behalf of the California State Legislature, ...\"

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
            "Formatted_Date": format_certificate_date(parsed.get("date_raw") or event_date),
            "Tone_Category": categorize_tone(parsed["title"])
        })

except Exception as e:
    st.error(f"⚠️ GPT failed: {e}. Using fallback row.")
    cert_rows.append({
        "Name": "UNKNOWN",
        "Title": "UNKNOWN",
        "Organization": "UNKNOWN",
        "Certificate_Text": fallback_commendation("UNKNOWN", "UNKNOWN", "UNKNOWN"),
        "Formatted_Date": format_certificate_date(event_date),
        "Tone_Category": "\U0001F4DD Recognition"
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
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_data = csv_buffer.getvalue()

    st.download_button(
        label="📊 Download CSV",
        data=csv_data,
        file_name="Certificates_MailMerge.csv",
        mime="text/csv"
    )

# ─── WORD GENERATION ───────────────────────────────────
if st.button("🛠 Generate Word Certificates from GitHub Template"):
    template_file = load_template_from_github(GITHUB_TEMPLATE_URL)
    if template_file:
        try:
            template_doc = Document(template_file)
            output_doc = Document()
            output_doc._body.clear_content()

            for _, row in pd.DataFrame(cert_rows).iterrows():
                cert = deepcopy(template_doc)

                for para in cert.paragraphs:
                    for key in row.index:
                        placeholder = f"{{{{{key}}}}}"
                        if placeholder in para.text:
                            for run in para.runs:
                                if placeholder in run.text:
                                    run.text = run.text.replace(placeholder, str(row[key]))

                for element in cert.element.body:
                    output_doc.element.body.append(element)
                output_doc.add_page_break()

            output_buffer = io.BytesIO()
            output_doc.save(output_buffer)
            output_buffer.seek(0)

            st.download_button(
                label="📥 Download Word Certificates (.docx)",
                data=output_buffer,
                file_name="Certificates_Output.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        except Exception as e:
            st.error(f"⚠️ Failed to generate Word file: {e}")
