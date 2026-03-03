# ---------------- PDF REPORT ----------------
st.subheader("📄 Download Professional PDF Report")

def generate_pdf():

    file_path = "NEW_STYLED_REPORT.pdf"   # <- fixed filename (no temp file confusion)

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    # BIG CLEAR TITLE (So you KNOW change happened)
    elements.append(Paragraph("<b>VERSION 3.0 – UPDATED REPORT</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(
        f"{user['company']} - Financial Intelligence Report",
        styles["Heading1"]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph(
        f"Finance Lead: {user['lead']}",
        styles["Normal"]))

    elements.append(Paragraph(
        f"Generated On: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
        styles["Normal"]))
    elements.append(Spacer(1, 25))

    # Table Data
    data = [
        ["Metric", "Value"],
        ["AI Risk Score (300-900)", str(risk_score)],
        ["Credit Risk", "High Risk" if credit_risk else "Low Risk"],
        ["Financial Stability", f"{financial_stability:.2f}"]
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("ALIGN",(0,0),(-1,-1),"CENTER")
    ]))

    elements.append(table)

    doc.build(elements)

    return file_path


if st.button("Generate & Download PDF"):
    pdf_path = generate_pdf()

    with open(pdf_path, "rb") as f:
        st.download_button(
            "Download Updated Report",
            f,
            file_name="UPDATED_Finance_Report.pdf",
            mime="application/pdf"
        )
