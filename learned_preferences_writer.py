import json
from collections import Counter
from pathlib import Path

def extract_phrases(text):
    """Extract commonly used ending phrases or key lines."""
    lines = text.strip().split("\n")
    return [line.strip() for line in lines if len(line.strip()) > 10]

def summarize_logs(log_dir="logs", output_file="learned_preferences.json", top_n=5):
    log_path = Path(log_dir)
    if not log_path.exists():
        print("No logs found.")
        return

    endings = Counter()
    tone_notes = set()

    for log_file in log_path.glob("cert_logs_*.jsonl"):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if not entry.get("approved"): continue
                    final_text = entry.get("final_commendation", "").strip()

                    # Phrase frequency
                    phrases = extract_phrases(final_text)
                    endings.update(phrases)

                    # Common tone markers
                    if "best wishes" in final_text.lower() or "all the best" in final_text.lower():
                        tone_notes.add("Closing: Friendly")
                    if "dedication" in final_text.lower() or "service" in final_text.lower():
                        tone_notes.add("Theme: Service and Impact")

                    if "community" in final_text.lower():
                        tone_notes.add("Focus: Community")

                except json.JSONDecodeError:
                    continue

    # Write to JSON
    summary = {
        "common_phrases": [phrase for phrase, _ in endings.most_common(top_n)],
        "tone_preferences": sorted(list(tone_notes)),
        "notes": "This file is auto-generated from approved certificate logs."
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved learned preferences to {output_file}")

if __name__ == "__main__":
    summarize_logs()
