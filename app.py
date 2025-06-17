import streamlit as st
import re, os, json, tempfile, io
from datetime import datetime
import pandas as pd
from pdfminer.high_level import extract_text
import openai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

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

# ─── GPT PROMPT ─────────────────────────────────────────
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
[
  {{
    "name": "Jane Smith",
    "title": "Volunteer of the Year",
    "organization": "Good Neighbors Foundation",
    "date_raw": "June 12, 2025",
    "commendation": "On behalf of the California State Legislature, congratulations on being named Volunteer of the Year. Your service to Good Neighbors Foundation is deeply appreciated."
  }}
]
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
    st.download_button(
        label="📊 Download CSV",
        data=csv_buffer.getvalue(),
        file_name="Certificates_MailMerge.csv",
        mime="text/csv"
    )

# ─── GENERATE WORD ──────────────────────────────────────
def generate_word_certificates(entries, template_path="template.docx"):
    merged_doc = Document()
    for i, row in enumerate(entries):
        spacer = merged_doc.add_paragraph()
        spacer.paragraph_format.space_before = Pt(300)

        para_name = merged_doc.add_paragraph()
        para_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_name = para_name.add_run(row["Name"])
        run_name.font.name = "Times New Roman"
        run_name.font.bold = True
        name_length = len(row["Name"])
        size = 60 if name_length <= 12 else 48 if name_length <= 18 else 40 if name_length <= 24 else 32 if name_length <= 30 else 28
        run_name.font.size = Pt(size)
        para_name.paragraph_format.space_after = Pt(2)

        if row["Organization"].strip():
            para_org = merged_doc.add_paragraph()
            para_org.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_org = para_org.add_run(row["Organization"])
            run_org.font.name = "Times New Roman"
            run_org.font.size = Pt(16)
            para_org.paragraph_format.space_after = Pt(16)

        para_text = merged_doc.add_paragraph()
        para_text.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para_text.paragraph_format.space_before = Pt(20)
        run_text = para_text.add_run(row["Certificate_Text"])
        run_text.font.name = "Times New Roman"
        run_text.font.size = Pt(14)

        if row.get("Formatted_Date"):
            for line in row["Formatted_Date"].split("\n"):
                para_date = merged_doc.add_paragraph()
                para_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
                para_date.paragraph_format.space_before = Pt(20)
                run_date = para_date.add_run(line)
                run_date.font.name = "Times New Roman"
                run_date.font.size = Pt(10)

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
