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

st.set_page_config(layout="centered")
st.title("📑 Certificate Review Assistant")

st.markdown("### 📎 Step 1: Upload a certificate request PDF or paste text")
pdf_file = st.file_uploader("Upload PDF (optional)", type=["pdf"])
text_input = st.text_area("Or paste certificate request text here", height=300)

if not pdf_file and not text_input.strip():
    st.warning("Please upload a PDF or paste text to continue.")
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
- If more than one name or organization appears in a single entry (e.g., "Jane Smith and John Doe"), set "possible_split": true
- If you're uncertain about the correct value for name, title, or organization, return multiple options inside an "alternatives" dictionary

Each certificate must include:
- name
- title (award or position — do NOT use "Certificate of Recognition")
- organization (if applicable)
- date_raw (use the event date if no specific date is listed)
- commendation: a 2–3 sentence message beginning with "On behalf of the California State Legislature..." that reflects what the recipient is being honored for, ties to the community or cause, and ends with well wishes
- optional: possible_split (true/false)
- optional: alternatives (dictionary of possible values for name, title, org, etc.)

The event date is: {event_date}

Return ONLY the JSON in this format:
[{{"name": "Jane Smith", "title": "Volunteer of the Year", "organization": "Good Neighbors Foundation", "date_raw": "June 12, 2025", "commendation": "...", "possible_split": true, "alternatives": {{ "name": ["Jane Smith", "John Doe"] }} }}]
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
        if parsed["title"].strip().lower() == "certificate of recognition":
            parsed["title"] = ""

        commendation = parsed.get("commendation", "").strip()
        if not commendation:
            commendation = enhanced_commendation(parsed["name"], parsed["title"], parsed["organization"])

        cert_rows.append({
            **parsed,
            "Certificate_Text": commendation,
            "Formatted_Date": format_certificate_date(parsed.get("date_raw") or event_date),
            "Tone_Category": "📝"  # Placeholder
        })

except Exception as e:
    st.error("⚠️ GPT failed to extract entries.")
    st.text(str(e))
    st.stop()
# ─── REVIEW ASSISTANT ─────────────────────────────────────────────────
st.subheader("👁 Review, Edit, and Approve Each Certificate")
final_cert_rows = []

for i, cert in enumerate(cert_rows, 1):
    with st.expander(f"📝 {cert['Name']} – {cert['Title']}"):

        # SPLIT SUGGESTION
        if cert.get("possible_split"):
            st.warning("⚠️ This entry may include multiple recipients.")
            decision = st.radio("Would you like to split this into two?", ["Keep as one", "Split into two"], key=f"split_{i}")
            if decision == "Split into two" and cert.get("alternatives", {}).get("name"):
                for alt_name in cert["alternatives"]["name"]:
                    st.markdown(f"### 🎓 Certificate for {alt_name}")
                    name = st.text_input("Name", value=alt_name, key=f"name_{i}_{alt_name}")
                    title = st.text_input("Title", value=cert["title"], key=f"title_{i}_{alt_name}")
                    org = st.text_input("Organization", value=cert["organization"], key=f"org_{i}_{alt_name}")
                    text = st.text_area("📜 Commendation", cert["Certificate_Text"], height=100, key=f"text_{i}_{alt_name}")
                    approved = st.checkbox("✅ Approve", value=True, key=f"approve_{i}_{alt_name}")
                    final_cert_rows.append({
                        "approved": approved,
                        "Name": name,
                        "Title": title,
                        "Organization": org,
                        "Certificate_Text": text,
                        "Formatted_Date": cert["Formatted_Date"],
                        "Tone_Category": cert["Tone_Category"]
                    })
                continue  # Skip rest of this loop

        # ALTERNATIVE SELECTORS (if available)
        alt = cert.get("alternatives", {})
        name = st.selectbox("Name", options=alt.get("name", [cert["name"]]), key=f"name_{i}")
        title = st.selectbox("Title", options=alt.get("title", [cert["title"]]), key=f"title_{i}")
        org = st.selectbox("Organization", options=alt.get("organization", [cert["organization"]]), key=f"org_{i}")
        text = st.text_area("📜 Commendation", cert["Certificate_Text"], height=100, key=f"text_{i}")
        approved = st.checkbox("✅ Approve this certificate", value=True, key=f"approve_{i}")

        final_cert_rows.append({
            "approved": approved,
            "Name": name,
            "Title": title,
            "Organization": org,
            "Certificate_Text": text,
            "Formatted_Date": cert["Formatted_Date"],
            "Tone_Category": cert["Tone_Category"]
        })

        # LIVE PREVIEW
        st.markdown("---")
        st.markdown("#### 📄 Certificate Preview")
        preview_lines = []

        preview_lines.append(f"<div style='text-align:center; font-size:48px; font-weight:bold;'>{name}</div>")
        if title.strip():
            preview_lines.append(f"<div style='text-align:center; font-size:28px; font-weight:bold;'>{title}</div>")
        if org.strip():
            preview_lines.append(f"<div style='text-align:center; font-size:18px;'>{org}</div>")

        preview_lines.append(f"<div style='text-align:center; font-size:16px; margin-top:30px;'>{text.replace(chr(10), '<br>')}</div>")

        for line in cert["Formatted_Date"].split("\n"):
            preview_lines.append(f"<div style='text-align:center; font-size:12px; margin-top:20px;'>{line}</div>")

        preview_lines.append("<br>" * 5)
        preview_lines.append(f"<div style='text-align:right; font-size:12px;'>_____________________________________</div>")
        preview_lines.append(f"<div style='text-align:right; font-size:14px;'>Stan Ellis</div>")
        preview_lines.append(f"<div style='text-align:right; font-size:14px;'>Assemblyman, 32nd District</div>")

        st.markdown("<br>".join(preview_lines), unsafe_allow_html=True)

# ─── WORD GENERATION ───────────────────────────────────────────────
def generate_word_certificates(entries):
    doc = Document()

    for i, entry in enumerate(entries):
        if i > 0:
            doc.add_page_break()

        doc.add_paragraph("\n" * 14).runs[0].font.size = Pt(12)

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
            pad = doc.add_paragraph(" ")
            pad.paragraph_format.space_before = Pt(0)
            pad.paragraph_format.space_after = Pt(0)
            pad.runs[0].font.size = Pt(12)

        for line, size in [
            ("_____________________________________", 12),
            ("Stan Ellis", 14),
            ("Assemblyman, 32nd District", 14)
        ]:
            p_sig = doc.add_paragraph(line)
            p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p_sig.paragraph_format.space_before = Pt(0)
            p_sig.paragraph_format.space_after = Pt(0)
            p_sig.runs[0].font.name = "Times New Roman"
            p_sig.runs[0].font.size = Pt(size)

    return doc

# ─── GENERATE WORD DOC BUTTON ──────────────────────────────────────
if st.button("📄 Generate Word Certificates"):
    approved_entries = [c for c in final_cert_rows if c["approved"]]
    if not approved_entries:
        st.error("No certificates approved.")
    else:
        with st.spinner("Generating Word document..."):
            doc = generate_word_certificates(approved_entries)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            doc.save(tmp.name)
            tmp.seek(0)
            st.download_button(
                label="⬇️ Download Certificates",
                data=tmp.read(),
                file_name="Certificates.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
