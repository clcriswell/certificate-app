import streamlit as st
import re, os, json, tempfile, io
from datetime import datetime
import pandas as pd
from pdfminer.high_level import extract_text
import openai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ─── CONFIG ─────────────────────────────────────────────
client = openai.OpenAI()
OPENAI_MODEL = "gpt-4o"

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
        return "🏆 Award"
    elif any(kw in title_lower for kw in ["president", "officer", "board", "service", "chair", "director"]):
        return "👥 Service"
    elif any(kw in title_lower for kw in ["opening", "grand", "event", "dedication", "launch"]):
        return "🏛 Event"
    elif any(kw in title_lower for kw in ["graduate", "class of", "commencement"]):
        return "🎓 Graduation"
    else:
        return "📝 Recognition"

def extract_event_date(text):
    match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d{2}", text)
    if match:
        return match.group(0)
    match = re.search(r"\d{1,2}/\d{1,2}/20\d{2}", text)
    if match:
        return match.group(0)
    return "unknown"

def determine_font_size(field, value):
    base_size = {
        "Name": 32,
        "Certificate_Text": 16,
        "Formatted_Date": 14,
        "Title": 18,
        "Organization": 14
    }.get(field, 12)

    if field == "Name":
        return max(20, base_size - int(len(value) / 2))
    elif field == "Certificate_Text":
        return max(12, base_size - int(len(value) / 10))
    else:
        return base_size

# ─── UI SETUP ───────────────────────────────────────────
st.set_page_config(layout="centered")
st.title("📑 Certificate CSV Generator (Multi-Entry)")
st.markdown("Upload a PDF certificate request and preview all auto-extracted entries before downloading a CSV.")

pdf_file = st.file_uploader("📎 Upload Certificate Request PDF", type=["pdf"])
if not pdf_file:
    st.stop()

with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
    tmp.write(pdf_file.read())
    tmp_path = tmp.name
pdf_text = extract_text(tmp_path)
os.remove(tmp_path)

event_date = extract_event_date(pdf_text)

SYSTEM_PROMPT = f"""
You will be given the full text of a certificate request. Your job is to extract ALL the individual certificates mentioned.

The event date for this request is: {event_date}

For each certificate, return:
- name
- title (award or position)
- organization
- date_raw (use the event date if no specific date is mentioned per recipient)
- commendation: A 1–2 sentence formal message starting with "On behalf of the California State Legislature, ..."

Respond only with JSON in this format:
[{{"name": "Jane Smith","title": "Volunteer of the Year","organization": "Good Neighbors Foundation","date_raw": "June 12, 2025","commendation": "On behalf of the California State Legislature, congratulations on being named Volunteer of the Year. Your service to Good Neighbors Foundation is deeply appreciated."}}]

DO NOT include markdown (like ```), explanations, or extra text.
"""

cert_rows = []

try:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pdf_text}
        ],
        temperature=0
    )

    content = response.choices[0].message.content
    cleaned = content.strip().removeprefix("```json").removesuffix("```").strip()

    with st.expander("🧾 Show Raw GPT Output (Debug)", expanded=False):
        st.code(content, language="json")

    parsed_entries = json.loads(cleaned)

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
    st.error("⚠️ GPT failed to extract entries.")
    st.text("No content received. Exception details:")
    st.text(str(e))

# ─── PREVIEW ────────────────────────────────────────────
st.subheader("👁 Preview Extracted Certificates")
for i, cert in enumerate(cert_rows, 1):
    with st.expander(f"{cert['Tone_Category']} #{i}: {cert['Name']} – {cert['Title']}"):
        st.write(f"**Organization:** {cert['Organization']}")
        st.write(f"**Date:** {cert['Formatted_Date']}")
        st.text_area("📜 Commendation", cert["Certificate_Text"], height=100, key=f"commendation_{i}")

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

# ─── Generate Certificates in Word ─────────────────────────────────────
def generate_word_certificates(entries, template_path="template.docx"):
    merged_doc = Document()

    for i, row in enumerate(entries):
        temp_doc = Document(template_path)

        # Spacer to push content halfway down the page
        top_spacer = merged_doc.add_paragraph()
        top_spacer.paragraph_format.space_before = Pt(200)

        for para in temp_doc.paragraphs:
            new_para = merged_doc.add_paragraph()
            is_signature = "{{Signature_Block}}" in para.text

            for run in para.runs:
                text = run.text

                if "{{Signature_Block}}" in text:
                    for line_text in [
                        "__________________________________________",
                        "Stan Ellis",
                        "Assemblyman, 32nd District"
                    ]:
                        sig_para = merged_doc.add_paragraph(line_text)
                        sig_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                        sig_para.paragraph_format.space_before = Pt(20)
                        sig_run = sig_para.runs[0]
                        sig_run.font.name = "Times New Roman"
                        sig_run.font.size = Pt(12)
                    break

                for key, value in row.items():
                    placeholder = f"{{{{{key}}}}}"
                    if placeholder in text:
                        text = text.replace(placeholder, str(value))
                        new_run = new_para.add_run(text)
                        new_run.font.name = "Times New Roman"

                        # Style each element
                        if key == "Name":
    name_length = len(str(value))
    if name_length <= 12:
        size = 64
    elif name_length <= 18:
        size = 52
    elif name_length <= 24:
        size = 44
    elif name_length <= 30:
        size = 36
    else:
        size = 28  # fallback for extra-long names
    new_run.font.bold = True
    new_run.font.size = Pt(size)
    new_para.paragraph_format.space_after = Pt(2)

                        elif key == "Title":
                            new_run.font.bold = True
                            new_run.font.size = Pt(18)
                        elif key == "Certificate_Text":
                            new_run.font.size = Pt(16)
                            new_para.paragraph_format.space_before = Pt(20)
                        elif key == "Formatted_Date":
                            new_run.font.size = Pt(10)  # Smaller date
                            new_para.paragraph_format.space_before = Pt(20)
                        else:
                            new_run.font.size = Pt(12)
                        break
                else:
                    new_run = new_para.add_run(text)
                    new_run.font.size = run.font.size
                    new_run.font.name = run.font.name
                    new_run.bold = run.bold
                    new_run.italic = run.italic
                    new_run.underline = run.underline

            if not is_signature:
                new_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if i < len(entries) - 1:
            merged_doc.add_page_break()

    return merged_doc


if st.button("📄 Generate Word Certificates"):
    with st.spinner("Generating Word document..."):
        doc = generate_word_certificates(cert_rows)
        temp_word = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        doc.save(temp_word.name)
        temp_word.seek(0)

        st.download_button(
            label="⬇️ Download Word Certificates",
            data=temp_word.read(),
            file_name="Certificates.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
