from fpdf import FPDF
import io
import csv
from io import BytesIO
import textwrap

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Resume Ranking Report", ln=True, align="C")
        self.ln(5)

def generate_pdf_report_with_explanations(job_title, candidates):
    pdf = PDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_title(f"Resume Ranking Report for {job_title}")  # 💡 Metadata
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Resume Ranking Report for {job_title}", ln=True, align="C")
    pdf.ln(5)

    headers = ["Rank", "Name", "Email", "Phone", "Skills", "Resume File", "Match %", "Explanation"]
    widths = [10, 30, 45, 30, 45, 35, 15, 100]

    def draw_table_header():
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(220, 230, 250)  # Light blue
        for i, header in enumerate(headers):
            pdf.cell(widths[i], 8, header, 1, 0, 'C', fill=True)
        pdf.ln()

    draw_table_header()
    pdf.set_font("Helvetica", "", 9)

    for idx, candidate in enumerate(candidates, 1):
        if (idx - 1) % 10 == 0 and idx != 1:
            pdf.add_page()
            draw_table_header()

        name = candidate.get("name", "N/A")
        email = candidate.get("email", "N/A")
        phone = candidate.get("phone", "N/A")
        skills = ', '.join(candidate.get("parsed_data", {}).get("skills", []))[:40]
        file_name = candidate.get("file_name", "N/A")
        match_score = f"{candidate.get('match_score', 0)}%"
        explanation = candidate.get("explanation", "No explanation available.")
        explanation_clean = explanation.encode("latin-1", "ignore").decode("latin-1")

        # 💡 More readable explanation wrap
        wrapped_explanation = "\n".join(textwrap.wrap(explanation_clean, 90))

        row_data = [
            str(idx),
            name[:30],
            email[:45],
            phone[:30],
            skills,
            file_name[:35],
            match_score,
            wrapped_explanation
        ]

        row_height = max(6, pdf.get_string_width(wrapped_explanation) // widths[7] * 6 + 6)

        for i, cell in enumerate(row_data):
            if i == 7:
                x, y = pdf.get_x(), pdf.get_y()
                pdf.multi_cell(widths[i], 5, cell, 1)
                pdf.set_xy(x + widths[i], y)
            else:
                pdf.cell(widths[i], row_height, cell, 1)

        pdf.ln()

    # 💡 Return stream (for download button in Streamlit)
    return BytesIO(pdf.output(dest='S'))

def generate_csv_report_with_explanations(job_title, candidates):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Rank", "Name", "Email", "Phone", "Match Score", "Skills", "Resume File", "Explanation"])

    for idx, candidate in enumerate(candidates, 1):
        explanation = candidate.get('explanation', '').replace("\n", " | ").replace("\r", " ").strip()

        # Truncate long explanations
        max_len = 300
        if len(explanation) > max_len:
            explanation = explanation[:max_len] + "..."

        writer.writerow([
            idx,
            candidate.get('name', 'N/A'),
            candidate.get('email', 'N/A'),
            candidate.get('phone', 'N/A'),
            f"{candidate.get('match_score', 0)}%",
            ', '.join(candidate.get('parsed_data', {}).get('skills', [])),
            candidate.get('file_name', 'N/A'),
            explanation
        ])

    return output.getvalue()
