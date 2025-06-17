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

def enhanced_commendation(name, title, org):
    base = f"On behalf of the California State Legislature, congratulations on being recognized as {title} with {org}."
    middle = "This honor reflects your dedication and the meaningful contributions you’ve made to our community."
    close = "I wish you all the best in your future endeavors."
    return f"{base} {middle} {close}"

def extract_event_date(text):
    match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d{2}", text)
    if match:
        return match.group(0)
    match = re.search(r"\d{1,2}/\d{1,2}/20\d{2}", text)
    if match:
        return match.group(0)
    return "unknown"

def determine_name_font_size(name):
    length = len(name)
    if length <= 12: return 60
    if length <= 18: return 48
    if length <= 24: return 40
    if length <= 30: return 34
    return 28

def determine_title_font_size(title):
    length = len(title)
    if length <= 20: return 28
    if length <= 30: return 24
    if length <= 36: return 20
    return 18

# ─── UI SETUP ───────────────────────────────────────────
st.set_page_config(layout="centered")
st.title("📑 Certificate CSV Generator (Multi-Entry)")
st.markdown("Upload a PDF certificate request and preview all auto-extracted entries before downloading.")

st.markdown("### 📎 Step 1: Upload a certificate request PDF or paste text")

pdf_file = st.file_uploader("Upload PDF (optional)", type=["pdf"])
text_input = st.text_area("Or paste certificate request text here", height=300)

if not pdf_file and not text_input.strip():
    st.warning("Please upload a PDF or paste text to continue.")
    st.stop()

# ─── TEXT EXTRACTION ───────────────────────────────────
if pdf_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name
    pdf_text = extract_text(tmp_path)
    os.remove(tmp_path)
else:
    pdf_text = text_input


event_date = extract_event_date(pdf_text)

SYSTEM_PROMPT = f"""
You will be given the full text of a certificate request. Your job is to extract ALL the individual certificates mentioned.

The event date for this request is: {event_date}

For each certificate, return:
- name
- title (award or position)
- organization
- date_raw (use the event date if no specific date is mentioned per recipient)
- commendation: A 2–3 sentence formal message that begins with "On behalf of the California State Legislature, ..." and includes a congratulatory statement, a community value reflection, and a closing best wishes sentence.

Respond only with JSON in this format:
[
  {{
    "name": "Jane Smith",
    "title": "Volunteer of the Year",
    "organization": "Good Neighbors Foundation",
    "date_raw": "June 12, 2025",
    "commendation": "On behalf of the California State Legislature, congratulations on being named Volunteer of the Year. Your service to Good Neighbors Foundation is deeply appreciated. I wish you all the best in your future endeavors."
  }}
]

DO NOT include markdown, explanations, or extra text.
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
        if parsed["title"].strip().lower() == "certificate of recognition":
            parsed["title"] = ""

        commendation = parsed.get("commendation", "").strip()
        if not commendation:
            commendation = enhanced_commendation(parsed["name"], parsed["title"], parsed["organization"])

        cert_rows.append({
            "Name": parsed["name"],
            "Title": parsed["title"],
            "Organization": parsed["organization"],
            "Certificate_Text": commendation,
            "Formatted_Date": format_certificate_date(parsed.get("date_raw") or event_date),
            "Tone_Category": categorize_tone(parsed["title"])
        })

except Exception as e:
    st.error("⚠️ GPT failed to extract entries.")
    st.text(str(e))

# ─── PREVIEW ────────────────────────────────────────────
st.subheader("👁 Preview Extracted Certificates")
for i, cert in enumerate(cert_rows, 1):
    with st.expander(f"{cert['Tone_Category']} #{i}: {cert['Name']} – {cert['Title']}"):
        st.write(f"**Organization:** {cert['Organization']}")
        st.write(f"**Date:** {cert['Formatted_Date']}")
        st.text_area("📜 Commendation", cert["Certificate_Text"], height=100, key=f"commendation_{i}")

# ─── WORD CERTIFICATE GENERATION ───────────────────────
def generate_word_certificates(entries, template_path="template.docx"):
    doc = Document()

    for i, entry in enumerate(entries):
        if i > 0:
            doc.add_page_break()

        doc.add_paragraph("\n" * 14).runs[0].font.size = Pt(12)

        p_name = doc.add_paragraph(entry["Name"])
        p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p_name.runs[0]
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(determine_name_font_size(entry["Name"]))
        p_name.paragraph_format.space_after = Pt(6)

        if entry["Title"].strip():
            p_title = doc.add_paragraph(entry["Title"])
            p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p_title.runs[0]
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(determine_title_font_size(entry["Title"]))

        p_text = doc.add_paragraph(entry["Certificate_Text"])
        p_text.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_text.paragraph_format.space_before = Pt(20)
        run = p_text.runs[0]
        run.font.name = "Times New Roman"
        run.font.size = Pt(14)

        date_lines = entry["Formatted_Date"].split("\n")
        for idx, line in enumerate(date_lines):
            p_date = doc.add_paragraph(line)
            p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_date.paragraph_format.space_before = Pt(0 if idx > 0 else 20)
            p_date.paragraph_format.space_after = Pt(0)
            run = p_date.runs[0]
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)

        for _ in range(5):
            p_pad = doc.add_paragraph(" ")
            p_pad.paragraph_format.space_before = Pt(0)
            p_pad.paragraph_format.space_after = Pt(0)
            p_pad.runs[0].font.size = Pt(12)

        for line, size in [
            ("_____________________________________", 12),
            ("Stan Ellis", 14),
            ("Assemblyman, 32nd District", 14)
        ]:
            p_sig = doc.add_paragraph(line)
            p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p_sig.paragraph_format.space_before = Pt(0)
            p_sig.paragraph_format.space_after = Pt(0)
            run = p_sig.runs[0]
            run.font.name = "Times New Roman"
            run.font.size = Pt(size)

    return doc

# ─── STREAMLIT ACTION BUTTON ───────────────────────────
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
