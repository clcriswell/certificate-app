import streamlit as st
import pdfplumber, re, tempfile, os
from docx import Document
from io import BytesIO
from openai import OpenAI

# 0 ─────────────── CONFIG ────────────────────────────────────────────────────
OPENAI_MODEL = "gpt-4o-mini"   # fastest, counts toward Pro quota
# (Switch to "gpt-4o" for maximum quality on extraction-language edge cases)

client = OpenAI()              # key automatically read from Streamlit secrets

# 1 ──────────────── SIDEBAR ──────────────────────────────────────────────────
st.sidebar.header("Certificate Generator v0.1")
st.sidebar.markdown("Upload a **PDF** request *or* paste request text below.")

# 2 ──────────────── INPUT AREA ───────────────────────────────────────────────
pdf_file = st.file_uploader("Upload request PDF", type=["pdf"])
text_input = st.text_area("…or paste request text", height=200)

if (not pdf_file) and (text_input.strip() == ""):
    st.stop()

# 3 ──────────────── EXTRACT TEXT FROM PDF IF NEEDED ─────────────────────────
raw_text = ""
if pdf_file:
    with pdfplumber.open(pdf_file) as pdf:
        raw_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
else:
    raw_text = text_input

# 4 ──────────────── NAÏVE FIELD PARSE (REGEX) ───────────────────────────────
def rule_based_extract(text: str) -> dict:
    """
    Very simple starter rules. Tune for your sample PDFs.
    """
    name     = re.search(r"Name[:\-]\s*(.+)", text, re.I)
    title    = re.search(r"Title[:\-]\s*(.+)", text, re.I)
    occasion = re.search(r"(Occasion|Event)[:\-]\s*(.+)", text, re.I)
    date     = re.search(r"Date[:\-]\s*(.+)", text, re.I)
    return {
        "Name":     name.group(1).strip()     if name else "",
        "Title":    title.group(1).strip()    if title else "",
        "Occasion": occasion.group(2).strip() if occasion else "",
        "Date":     date.group(1).strip()     if date else "",
    }

fields = rule_based_extract(raw_text)

# 5 ──────────────── OPTIONAL GPT‑4o CLEAN‑UP ────────────────────────────────
with st.expander("💡 Extraction looks wrong?  (click to use GPT‑4o)"):
    if st.button("Improve using GPT‑4o (1 message)"):
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content":
                 "Extract the recipient's Name, professional Title, Occasion, and Date "
                 "from the following text. Return valid JSON with keys "
                 "name, title, occasion, date."},
                {"role": "user", "content": raw_text}
            ],
            temperature=0
        )
        try:
            improved = response.choices[0].message.content
            fields = {k.capitalize(): v for k, v in eval(improved).items()}
            st.success("Fields updated from GPT‑4o.")
        except Exception as e:
            st.error(f"GPT‑4o returned an unexpected format: {e}")

# 6 ──────────────── REVIEW / EDIT FORM (MAIL‑MERGE STYLE) ───────────────────
with st.form("review"):
    st.subheader("📝 Review & Edit")
    name     = st.text_input("Recipient Name",  value=fields["Name"])
    title    = st.text_input("Recipient Title", value=fields["Title"])
    occasion = st.text_input("Occasion",        value=fields["Occasion"])
    date     = st.text_input("Date",            value=fields["Date"])
    add_msg  = st.checkbox("Include draft certificate message language")
    submitted = st.form_submit_button("Generate Certificate")

if not submitted:
    st.stop()

# 7 ──────────────── FILL WORD TEMPLATE ──────────────────────────────────────
def fill_template(name, title, occasion, date, add_msg):
    doc = Document("cert_template.docx")
    replace_map = {
        "{{NAME}}":     name,
        "{{TITLE}}":    title,
        "{{OCCASION}}": occasion,
        "{{DATE}}":     date,
    }
    for p in doc.paragraphs:
        for key, val in replace_map.items():
            if key in p.text:
                inline = p.runs
                for i in range(len(inline)):
                    if key in inline[i].text:
                        inline[i].text = inline[i].text.replace(key, val)

    if add_msg:
        doc.add_paragraph(
            f"On behalf of Assemblymember Stan Ellis, we commend {name} "
            f"for {occasion} and thank you for your service to the community."
        )

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

doc_bytes = fill_template(name, title, occasion, date, add_msg)

# 8 ──────────────── DOWNLOAD BUTTON ─────────────────────────────────────────
st.success("Certificate ready!  Click below to download.")
st.download_button(
    label="📄 Download Word Document",
    data=doc_bytes,
    file_name=f"Certificate_{name.replace(' ', '_')}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
