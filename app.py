import streamlit as st
import re, os, json, tempfile
from datetime import datetime
import pandas as pd
from pdfminer.high_level import extract_text
import openai

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
        message = f"On behalf of the California State Legislature, congratulations on being recognized as {org}'s {title}. "
    elif any(kw in title_lower for kw in ["president", "board", "officer", "service", "chair", "director"]):
        message = f"On behalf of the California State Legislature, thank you for your service as {title} with {org}. "
    elif "opening" in title_lower or "grand" in title_lower:
        message = f"On behalf of the California State Legislature, congratulations on the opening of {org}. "
    elif "graduat" in title_lower:
        message = f"On behalf of the California State Legislature, congratulations on successfully graduating from {org}. "
    else:
        message = f"On behalf of the California State Legislature, we commend you for your accomplishments with {org}. "
    message += "This recognition speaks highly of your dedication and contributions to the community."
    return message

def categorize_tone(title):
    title_lower = title.lower()
    if any(kw in title_lower for kw in ["award", "of the year", "honoree", "achievement", "excellence", "inductee"]):
        return "🏆 Award"
    elif any(kw in title_lower for kw in ["president", "officer", "board", "director", "retire", "service", "chair"]):
        return "👥 Service"
    elif any(kw in title_lower for kw in ["opening", "grand", "event", "dedication", "launch"]):
        return "🏛 Event"
    elif any(kw in title_lower for kw in ["graduate", "class of", "commencement"]):
        return "🎓 Graduation"
    else:
        return "📝 Recognition"

# ─── STREAMLIT UI ───────────────────────────────────────
st.set_page_config(layout="centered")
st.title("📊 Certificate Data Extractor (Excel Mail Merge Mode)")
st.markdown("Upload a PDF with multiple recognition entries. This will extract and structure the data for mail merge in Excel.")

pdf_file = st.file_uploader("📎 Upload Multi-Request PDF", type=["pdf"])
if not pdf_file:
    st.stop()

# ─── TEXT EXTRACTION ────────────────────────────────────
with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
    tmp.write(pdf_file.read())
    tmp_path = tmp.name
pdf_text = extract_text(tmp_path)
os.remove(tmp_path)

entries = re.split(r"\_{5,}[\s\S]+?Stan Ellis\s+Assemblyman,? \d{1,2}(st|nd|rd|th)? District", pdf_text)
entries = [e.strip() for e in entries if e.strip()]
st.info(f"📄 {len(entries)} entries detected.")

# ─── PROCESS EACH ENTRY ─────────────────────────────────
data = []
for idx, entry in enumerate(entries):
    with st.spinner(f"🧠 Processing entry #{idx+1}..."):
        try:
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content":
                     "You will be given a recognition request. Extract:\n"
                     "• name\n• title (award or position)\n• organization\n• date_raw\n\n"
                     "Then generate a commendation starting with 'On behalf of the California State Legislature,' "
                     "that suits the tone (award, service, opening, graduation).\n\n"
                     "Return only valid JSON with keys: name, title, organization, date_raw, commendation."},
                    {"role": "user", "content": entry}
                ],
                temperature=0
            )
            raw = response["choices"][0]["message"]["content"].strip().strip("```json").strip("```")
            parsed = json.loads(raw)
            parsed["Formatted_Date"] = format_certificate_date(parsed["date_raw"])
            parsed["Tone_Category"] = categorize_tone(parsed["title"])
            data.append({
                "Name": parsed["name"],
                "Title": parsed["title"],
                "Organization": parsed["organization"],
                "Certificate_Text": parsed["commendation"],
                "Formatted_Date": parsed["Formatted_Date"],
                "Tone_Category": parsed["Tone_Category"]
            })
        except Exception:
            fallback = {
                "Name": "UNKNOWN",
                "Title": "UNKNOWN",
                "Organization": "UNKNOWN",
                "Certificate_Text": fallback_commendation("UNKNOWN", "UNKNOWN", "UNKNOWN"),
                "Formatted_Date": "Dated ______",
                "Tone_Category": "📝 Recognition"
            }
            data.append(fallback)

# ─── EXPORT TO EXCEL ────────────────────────────────────
if st.button("📥 Download Mail Merge Excel"):
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Certificates")
    output.seek(0)
    st.success("✅ Your Excel file is ready!")
    st.download_button(
        label="📊 Download Excel File",
        data=output,
        file_name="Certificates_MailMerge.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
