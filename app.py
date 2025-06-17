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
import random

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
    if title and not org:
        base = f"On behalf of the California State Legislature, congratulations on being recognized as {title}."
    elif org and not title:
        base = f"On behalf of the California State Legislature, congratulations on your recognition with {org}."
    elif title and org:
        base = f"On behalf of the California State Legislature, congratulations on being recognized as {title} with {org}."
    else:
        base = f"On behalf of the California State Legislature, congratulations on your well-deserved recognition."
    middle = "This honor reflects your dedication and the meaningful contributions you’ve made to our community."
    close = "I wish you all the best in your future endeavors."
    return f"{base} {middle} {close}"

def refine_commendation(name, title, org, comment):
    prompt = f"Rewrite the following commendation using the comment as guidance.\n\nName: {name}\nTitle: {title}\nOrganization: {org}\nComment: {comment.strip()}\n\nCommendation:"
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You refine official commendations based on input from a reviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None

def log_certificates(original_data, final_data, event_text, source="pasted", global_comment=""):
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
                "approved": True,
                "reviewer_comment": final.get("reviewer_comment", ""),
                "global_comment": global_comment
            }
            f.write(json.dumps(entry) + "\n")

def generate_word_certificates(entries):
    doc = Document()
    for i, entry in enumerate(entries):
        if i > 0:
            doc.add_page_break()

        p_spacer = doc.add_paragraph()
        p_spacer.paragraph_format.space_before = Pt(250)
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

# ─── APP START ───────────────────────────────────────────
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

SYSTEM_PROMPT = "Extract each individual certificate entry from the text and return structured JSON with name, title, organization, and commendation text."

try:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pdf_text}
        ]
    )
    content = response.choices[0].message.content.strip()
    cert_rows = json.loads(content.removeprefix("```json").removesuffix("```"))
    for cert in cert_rows:
        cert.setdefault("Certificate_Text", enhanced_commendation(cert.get("name", ""), cert.get("title", ""), cert.get("organization", "")))
        cert.setdefault("Formatted_Date", format_certificate_date(datetime.today().strftime("%B %d, %Y")))
except Exception as e:
    st.error("⚠️ Failed to process certificate entries.")
    st.stop()

# ─── GLOBAL COMMENT ──────────────────────────────────────
st.subheader("💬 Global Comments")
global_comment = st.text_area("Optional: Enter tone/style guidance to apply to all certificates:", key="global_comment")
refine_all = st.button("✨ Refine All Commendations with Global Comment")
if refine_all and global_comment.strip():
    for cert in cert_rows:
        updated = refine_commendation(cert["name"], cert["title"], cert["organization"], global_comment)
        if updated:
            cert["Certificate_Text"] = updated
    st.success("All commendations updated.")

# ─── REVIEW & APPROVE ────────────────────────────────────
st.subheader("👁 Review, Edit, and Approve Each Certificate")
final_cert_rows = []
hide_notes = st.checkbox("🔒 Hide reviewer notes from previews", value=True)

for i, cert in enumerate(cert_rows):
    with st.expander(f"📝 {cert['name']} – {cert['title']}"):
        name = st.text_input("Name", value=cert["name"], key=f"name_{i}")
        title = st.text_input("Title", value=cert["title"], key=f"title_{i}")
        org = st.text_input("Organization", value=cert["organization"], key=f"org_{i}")
        text = st.text_area("📜 Commendation", cert["Certificate_Text"], height=100, key=f"text_{i}")
        approved = st.checkbox("✅ Approve", value=True, key=f"approve_{i}")
        comment = st.text_area("✏️ Reviewer Comment", "", placeholder="Tone adjustment or rewrite guidance", key=f"comment_{i}")

        if st.button("✨ Refine This Certificate", key=f"refine_{i}") and comment.strip():
            new_text = refine_commendation(name, title, org, comment)
            if new_text:
                cert["Certificate_Text"] = new_text
                st.session_state[f"text_{i}"] = new_text
                st.success("Commendation refined.")

        cert.update({
            "Name": name,
            "Title": title,
            "Organization": org,
            "Certificate_Text": st.session_state.get(f"text_{i}", text),
            "Formatted_Date": cert["Formatted_Date"],
            "approved": approved,
            "reviewer_comment": comment
        })
        final_cert_rows.append(cert)

        st.markdown("#### 📄 Certificate Preview")
        preview_text = cert["Certificate_Text"].split("Note: ")[0] if hide_notes else cert["Certificate_Text"]
        st.markdown(f"<div style='text-align:center; font-size:16px'>{preview_text.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

# ─── FINAL OUTPUT ───────────────────────────────────────
if st.button("📄 Generate Word Certificates"):
    approved_entries = [c for c in final_cert_rows if c.get("approved")]
    if not approved_entries:
        st.error("No certificates were approved.")
    else:
        log_certificates(cert_rows, approved_entries, pdf_text, global_comment=global_comment)
        with st.spinner("Generating Word document..."):
            doc = generate_word_certificates(approved_entries)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            doc.save(tmp.name)
            tmp.seek(0)
            st.download_button("⬇️ Download Word Certificates", tmp.read(), "Certificates.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
