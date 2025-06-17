import streamlit as st
import re, os, json, tempfile, io
from datetime import datetime
from pathlib import Path
import pandas as pd
from pdfminer.high_level import extract_text
import openai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

client = openai.OpenAI()
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

def enhanced_commendation(name, title, org):
    base = f"On behalf of the California State Legislature, congratulations on being recognized as {title} with {org}."
    middle = "This honor reflects your dedication and the meaningful contributions you’ve made to our community."
    close = "I wish you all the best in your future endeavors."
    return f"{base} {middle} {close}"

def log_certificates(original_data, final_data, event_text, source="pasted"):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    log_file = log_dir / f"cert_logs_{timestamp[:10]}.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        for original, final in zip(original_data, final_data):
            if not final.get("approved"):
                continue
            entry = {
                "timestamp": timestamp,
                "source": source,
                "event_text": event_text[:1000],
                "original_name": original.get("name", ""),
                "final_name": final.get("Name", ""),
                "original_title": original.get("title", ""),
                "final_title": final.get("Title", ""),
                "original_organization": original.get("organization", ""),
                "final_organization": final.get("Organization", ""),
                "original_commendation": original.get("commendation", ""),
                "final_commendation": final.get("Certificate_Text", ""),
                "approved": True
            }
            f.write(json.dumps(entry) + "\n")

# ─── UI + INPUT ─────────────────────────────────────────
st.set_page_config(layout="centered")
st.title("📑 Certificate Review Assistant")

pdf_file = st.file_uploader("Upload PDF (optional)", type=["pdf"])
text_input = st.text_area("Or paste certificate request text here", height=300)

if not pdf_file and not text_input.strip():
    st.warning("Please upload a PDF or paste request text.")
    st.stop()

if pdf_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name
    pdf_text = extract_text(tmp_path)
    os.remove(tmp_path)
else:
    pdf_text = text_input

event_date = format_certificate_date(datetime.today().strftime("%B %d, %Y"))

SYSTEM_PROMPT = f"""
You will be given the full text of a certificate request. Your task is to extract ALL individual certificates mentioned, and for each one:

- Carefully interpret the context of the event and the nature of each person's recognition
- If more than one name or organization appears in a single entry, set "possible_split": true
- If you're uncertain about name, title, or org, return multiple options inside "alternatives"

Each certificate must include:
- name
- title (NOT "Certificate of Recognition")
- organization (if applicable)
- date_raw (or fallback to event date)
- commendation: 2–3 sentence message starting with “On behalf of the California State Legislature...” that honors their work and ends with well wishes
- optional: possible_split (true/false)
- optional: alternatives (dictionary)

The event date is: {event_date}

Return ONLY valid JSON.
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
    name = parsed.get("name") or "Recipient"
    title = parsed.get("title") or ""
    org = parsed.get("organization") or ""
    commendation = parsed.get("commendation") or ""

    # Remove redundant title
    if title.strip().lower() == "certificate of recognition":
        title = ""

    # Fallback commendation if GPT didn’t return one
    if not commendation.strip():
        commendation = enhanced_commendation(name, title, org)

    cert_rows.append({
        "Name": name,
        "Title": title,
        "Organization": org,
        "Certificate_Text": commendation,
        "Formatted_Date": format_certificate_date(parsed.get("date_raw") or event_date),
        "Tone_Category": "📝",
        "possible_split": parsed.get("possible_split", False),
        "alternatives": parsed.get("alternatives", {})
    })


except Exception as e:
    st.error("⚠️ GPT failed to extract entries.")
    st.text(str(e))
    st.stop()

# ─── REVIEW + PREVIEW UI ─────────────────────────────────────
st.subheader("👁 Review, Edit, and Approve Each Certificate")
final_cert_rows = []

for i, cert in enumerate(cert_rows, 1):
    with st.expander(f"📝 {cert['Name']} – {cert['Title']}"):

        if cert.get("possible_split"):
            st.warning("⚠️ This entry may include multiple recipients.")
            decision = st.radio("Would you like to split this?", ["Keep as one", "Split into two"], key=f"split_{i}")
            if decision == "Split into two" and cert.get("alternatives", {}).get("name"):
                for alt_name in cert["alternatives"]["name"]:
                    name = st.text_input("Name", value=alt_name, key=f"name_{i}_{alt_name}")
                    title = st.text_input("Title", value=cert["Title"], key=f"title_{i}_{alt_name}")
                    org = st.text_input("Organization", value=cert["Organization"], key=f"org_{i}_{alt_name}")
                    text = st.text_area("📜 Commendation", cert["Certificate_Text"], height=100, key=f"text_{i}_{alt_name}")
                    approved = st.checkbox("✅ Approve", value=True, key=f"approve_{i}_{alt_name}")
                    final_cert_rows.append({
                        "approved": approved, "Name": name, "Title": title,
                        "Organization": org, "Certificate_Text": text,
                        "Formatted_Date": cert["Formatted_Date"], "Tone_Category": cert["Tone_Category"]
                    })
                continue

        alt = cert.get("alternatives", {})
        name = st.selectbox("Name", options=alt.get("name", [cert["Name"]]), key=f"name_{i}")
        title = st.selectbox("Title", options=alt.get("title", [cert["Title"]]), key=f"title_{i}")
        org = st.selectbox("Organization", options=alt.get("organization", [cert["Organization"]]), key=f"org_{i}")
        text = st.text_area("📜 Commendation", cert["Certificate_Text"], height=100, key=f"text_{i}")
        approved = st.checkbox("✅ Approve this certificate", value=True, key=f"approve_{i}")

        final_cert_rows.append({
            "approved": approved, "Name": name, "Title": title,
            "Organization": org, "Certificate_Text": text,
            "Formatted_Date": cert["Formatted_Date"], "Tone_Category": cert["Tone_Category"]
        })

        # LIVE PREVIEW
        st.markdown("---")
        st.markdown("#### 📄 Certificate Preview")
        lines = []
        lines.append(f"<div style='text-align:center; font-size:48px; font-weight:bold;'>{name}</div>")
        if title.strip():
            lines.append(f"<div style='text-align:center; font-size:28px; font-weight:bold;'>{title}</div>")
        if org.strip():
            lines.append(f"<div style='text-align:center; font-size:18px;'>{org}</div>")
        lines.append(f"<div style='text-align:center; font-size:16px; margin-top:30px;'>{text.replace(chr(10), '<br>')}</div>")
        for line in cert["Formatted_Date"].split("\n"):
            lines.append(f"<div style='text-align:center; font-size:12px; margin-top:20px;'>{line}</div>")
        lines.append("<br>" * 5)
        lines.append(f"<div style='text-align:right; font-size:12px;'>_____________________________________</div>")
        lines.append(f"<div style='text-align:right; font-size:14px;'>Stan Ellis</div>")
        lines.append(f"<div style='text-align:right; font-size:14px;'>Assemblyman, 32nd District</div>")
        st.markdown("<br>".join(lines), unsafe_allow_html=True)

# ─── WORD GENERATION ─────────────────────────────────────
def generate_word_certificates(entries):
    doc = Document()
    for i, entry in enumerate(entries):
        if i > 0:
            doc.add_page_break()

        # Adjust top spacing based on commendation length
        text_line_count = entry["Certificate_Text"].count("\n") + len(entry["Certificate_Text"]) // 80
        spacer_lines = max(6, 14 - text_line_count)

        p_spacer = doc.add_paragraph()
        p_spacer.paragraph_format.space_before = Pt(spacer_lines * 12)
        p_spacer.add_run(" ").font.size = Pt(12)

        p_name = doc.add_paragraph(entry["Name"])
        p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_name.runs[0].bold = True
        p_name.runs[0].font.name = "Times New Roman"
        p_name.runs[0].font.size = Pt(determine_name_font_size(entry["Name"]))
        p_name.paragraph_format.space_after = Pt(6)

        if entry["Title"].strip():
            p_title = doc.add_paragraph(entry["Title"])
            p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_title.runs[0].bold = True
            p_title.runs[0].font.name = "Times New Roman"
            p_title.runs[0].font.size = Pt(determine_title_font_size(entry["Title"]))

        p_text = doc.add_paragraph(entry["Certificate_Text"])
        p_text.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_text.paragraph_format.space_before = Pt(20)
        p_text.runs[0].font.name = "Times New Roman"
        p_text.runs[0].font.size = Pt(14)

        for idx, line in enumerate(entry["Formatted_Date"].split("\n")):
            p_date = doc.add_paragraph(line)
            p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_date.paragraph_format.space_before = Pt(0 if idx > 0 else 20)
            p_date.paragraph_format.space_after = Pt(0)
            p_date.runs[0].font.name = "Times New Roman"
            p_date.runs[0].font.size = Pt(12)

        for _ in range(5):
            spacer = doc.add_paragraph(" ")
            spacer.paragraph_format.space_before = Pt(0)
            spacer.paragraph_format.space_after = Pt(0)
            spacer.runs[0].font.size = Pt(12)

        for line, size in [
            ("_____________________________________", 12),
            ("Stan Ellis", 14),
            ("Assemblyman, 32nd District", 14)
        ]:
            sig = doc.add_paragraph(line)
            sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            sig.paragraph_format.space_before = Pt(0)
            sig.paragraph_format.space_after = Pt(0)
            sig.runs[0].font.name = "Times New Roman"
            sig.runs[0].font.size = Pt(size)
    return doc

# ─── FINAL BUTTON ───────────────────────────────────────
if st.button("📄 Generate Word Certificates"):
    approved_entries = [c for c in final_cert_rows if c["approved"]]
    if not approved_entries:
        st.error("No certificates were approved.")
    else:
        log_certificates(parsed_entries, approved_entries, pdf_text, source="pdf" if pdf_file else "pasted")
        with st.spinner("Generating Word document..."):
            doc = generate_word_certificates(approved_entries)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            doc.save(tmp.name)
            tmp.seek(0)
            st.download_button(
                label="⬇️ Download Word Certificates",
                data=tmp.read(),
                file_name="Certificates.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
