import os
import json
from datetime import datetime

from core.theme import BRAND_OWNER, APP_VERSION, APP_NAME

BASE_DIR = os.path.join(os.path.expanduser("~"), "PrimeVitalsData")


def save_json_report(disk_name, data):
    folder = os.path.join(BASE_DIR, f"PrimeData_{disk_name.strip(':\\/')}")
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return filename


def export_html_report(all_data, output_path):
    html = ["<html><head><meta charset='utf-8'><title>Prime PC Vitals Report</title>",
            "<style>body{background:#0D0D0D;color:#E8E8E8;font-family:Segoe UI;} "
            "h1{color:#D4AF37;} h2{color:#B00020;} table{border-collapse:collapse;width:100%;} "
            "td,th{border:1px solid #1A1A40;padding:6px;}</style></head><body>"]
    html.append(f"<h1>{APP_NAME} — Full Report</h1><p>Generated: {datetime.now()}</p>")

    for section, content in all_data.items():
        html.append(f"<h2>{section}</h2>")
        if isinstance(content, list):
            if content and isinstance(content[0], dict):
                headers = content[0].keys()
                html.append("<table><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>")
                for row in content:
                    html.append("<tr>" + "".join(f"<td>{row.get(h,'')}</td>" for h in headers) + "</tr>")
                html.append("</table>")
            else:
                html.append("<ul>" + "".join(f"<li>{item}</li>" for item in content) + "</ul>")
        elif isinstance(content, dict):
            html.append("<table>")
            for k, v in content.items():
                html.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
            html.append("</table>")

    html.append(
        f"<hr style='border-color:#1A1A40;'><p style='text-align:center;color:#9A9A9A;'>"
        f"{BRAND_OWNER} &nbsp;|&nbsp; {APP_NAME} v{APP_VERSION}</p>"
    )
    html.append("</body></html>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    return output_path