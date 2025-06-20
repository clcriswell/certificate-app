def generate_html_report(data: dict) -> str:
    """Generate an HTML report string given the assistant result data."""
    answer = f"<h2>Final Answer</h2><p>{data['answer']}</p>"
    sources = "<h3>Sources</h3><ul>"
    for src in data["sources"]:
        title = src.get("title", "Untitled")
        url = src.get("url", "#")
        domain = src.get("source", "unknown")
        sources += f"<li><a href='{url}' target='_blank'>{title}</a> – {domain}</li>"
    sources += "</ul>"
    log = "<h3>Loop Decisions</h3><pre>" + "\n".join(data.get("analysis_log", [])) + "</pre>"
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Research Report</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; max-width: 900px; margin: 40px auto; }}
            h2, h3 {{ color: #2c3e50; }}
            ul {{ padding-left: 20px; }}
            pre {{ background: #f4f4f4; padding: 10px; border-left: 3px solid #ccc; }}
            a {{ color: #2980b9; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        {answer}
        {sources}
        {log}
    </body>
    </html>
    """
    return html.strip()
