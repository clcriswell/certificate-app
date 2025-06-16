import streamlit as st
import re, tempfile, os, json
from docx import Document
from io import BytesIO
import openai

# 🔐 Load API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
OPENAI_MODEL = "gpt-4o"

# ─────────────── UI: Sidebar
st.sidebar.header("Certificate Generator")
st.sidebar.markdown("Upload a **PDF** request or paste recognition text below.")

# ─────────────── Input
pdf_file = st.file_uploader("Upload request PDF", type=["pdf"])
text_input = st.text_area("…or paste request text", height=200)

if (not pdf_file) and (text_input.strip() == ""):
    st.stop()

# ─────────────── Extract text from PDF (if provided)
raw_text = ""
if pdf_file:
    from pdfminer.high_level import extract_text
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name
    raw_text = extract_text(tmp_path)
    os.remove(tmp_path)
else:
    raw_text = text_input

# ─────────────── Basic extraction using regex
def rule_based_extract(text: str) -> dict:
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

# ─────────────── Optional GPT‑4o fix
with st.expander("💡 Extraction looks wrong? Click here to use GPT‑4o"):
    if st.button("Improve using GPT‑4o"):
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content":
                 "Extract the recipient's Name, Title, Occasion, and Date from the text below. "
                 "Respond ONLY with valid JSON like this: "
                 "{\"name\": \"\", \"title\": \"\", \"occasion\": \"\", \"date\": \"\"}. "
                 "Do not add any explanation or notes."},
                {"role": "user", "content": raw_text}
            ],
            temperature=0
        )
        improved = response["choices"][0]["message"]["content"]
        try:
            cleaned = improved.strip().strip("```json").strip("```").strip()
            parsed = json.loads(cleaned)
            fields = {k.capitalize(): v for k, v in parsed.items()}
            st.success("Fields updated using GPT‑4o.")
        except json.JSONDecodeError as e:
            st.error(f"Could not parse GPT response as JSON: {e}")
            st.code(improved)

# ─────────────── Review and edit form
with st.form("review"):
    st.subheader("📝 Review Certificate Details")
    name     = st.text_input("Recipient Name",  value=fields["Name"])
    title    = st.text_input("Recipient Title", value=fields["Title"])
    occasion = st.text_input("Occasion",        value=fields["Occasion"])
    date     = st.text_input("Date",            value=fields["Date"])
    add_msg  = st.checkbox("Include a commendation message")
    submitted = st.form_submit_button("Generate Certificate")

if not submitted:
    st.stop()

# ─────────────── Fill Word template
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
                for run in p.runs:
                    if key in run.text:
                        run.text = run.text.replace(key, val)

    if add_msg:
        doc.add_paragraph(
            f"On behalf of Assemblymember Stan Ellis, we commend {name} "
            f"for {occasion} and thank you for your service to the community."
        )

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ─────────────── Export as download
doc_bytes = fill_template(name, title, occasion, date, add_msg)
st.success("🎉 Certificate ready!")
st.download_button(
    label="📄 Download Word Document",
    data=doc_bytes,
    file_name=f"Certificate_{re.sub(r'[^\w\\-]', '_', name)}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
