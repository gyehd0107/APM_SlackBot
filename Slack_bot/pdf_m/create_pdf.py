import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.pagesizes import letter, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Line
from Slack_bot.log_m.log import log

REPORT_TITLES = {
    "Daily": "Daily Report",
    "Weekly": "Weekly Report",
    "Monthly": "Monthly Report",
}


def save_report_pdf(
    graph_path,
    validation_results,
    acceptable_lower_bound,
    acceptable_upper_bound,
    cra,
    crb,
    report_type,
    time_difference,
    total_hours,
    total_cells,
    nan_cells,
    error_data,
    time_graph,
    pm_statistics
):
    year = cra[:4]
    month = cra[4:6]
    base_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "save",
            "report_pdf",
            year,
            month,
            report_type,
        )
    )
    os.makedirs(base_path, exist_ok=True)

    cra_formatted = datetime.strptime(cra, "%Y%m%dT%H%M%S").strftime("%Y-%m-%d")
    crb_formatted = datetime.strptime(crb, "%Y%m%dT%H%M%S").strftime("%Y-%m-%d")
    output_filename = os.path.join(base_path, f"{cra_formatted}~{crb_formatted}.pdf")

    # 메인 제목 설정
    main_title = REPORT_TITLES.get(report_type, "Monthly Report")

    pdf = SimpleDocTemplate(output_filename, pagesize=letter)
    styles = getSampleStyleSheet()

    # 스타일 정의
    main_title_style = ParagraphStyle("MainTitle", parent=styles["Title"], fontSize=16, alignment=1)
    sub_title_style = ParagraphStyle("SubTitle", parent=styles["Normal"], fontSize=12, alignment=2)
    sub2_title_style = ParagraphStyle("SubTitle", parent=styles["Normal"], fontSize=10)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=14)
    mid_style = ParagraphStyle("Mid", parent=styles["Heading3"], fontSize=12)
    
    elements = []

    # 메인 제목 추가
    main_title_text = Paragraph(f"<b>{main_title}</b>", main_title_style)
    elements.append(main_title_text)
    elements.append(Spacer(1, 0.2 * inch))

    # 구분선 추가
    line_drawing = Drawing(500, 1)
    line_drawing.add(Line(0, 0, 500, 0, strokeWidth=1, strokeColor=colors.black))
    elements.append(line_drawing)
    elements.append(Spacer(1, 0.2 * inch))

    # 날짜 정보 추가 (오른쪽 정렬)
    date_text = Paragraph(f"<b>{cra_formatted} ~ {crb_formatted}</b>", sub_title_style)
    elements.append(date_text)
    elements.append(Spacer(1, 0.1 * inch))

    # 데이터 수집 요약 섹션
    title = Paragraph(f"<b>1. {report_type} Data Collection Summary</b>", heading_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))

    time_difference_str = str(time_difference)
    time_difference_text = Paragraph(
        f"<b>- Total {report_type} Data Collection Time: {time_difference_str} ({total_hours:.0f} minute)</b>",
        sub2_title_style
    )
    elements.append(time_difference_text)
    elements.append(Spacer(1, 0.2 * inch))

    total_cells_text = Paragraph(
        f"<b>- Number of {report_type} Total Data Cells: {total_cells:.0f}</b>",
        sub2_title_style,
    )
    elements.append(total_cells_text)
    elements.append(Spacer(1, 0.2 * inch))

    nan_cells_text = Paragraph(f"<b>- Number of {report_type} Data NaNs: {nan_cells}</b>", sub2_title_style)
    elements.append(nan_cells_text)
    elements.append(Spacer(1, 0.2 * inch))

    # 에러 데이터 정보 테이블 추가
    if error_data:
        elements.append(Paragraph("<b>Error Data Details:</b>", mid_style))
        elements.append(Spacer(1, 0.1 * inch))
        for column, nan_rows in error_data:
            elements.append(Paragraph(f"<b>- Column:</b> {column}", sub2_title_style))
            # 테이블 헤더 및 데이터 구성
            table_data = [["APMdatetime", "RPMdatetime", "Value"]]
            table_data.extend(nan_rows.values.tolist())
            error_table = Table(table_data, colWidths=[150, 150, 150])
            error_table_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ])
            error_table.setStyle(error_table_style)
            elements.append(error_table)
            elements.append(Spacer(1, 0.2 * inch))

    # PM 센서 통계 테이블 추가
    table_data = [["Sensor", "Max", "Min", "Mean"]]
    for sensor, stats in pm_statistics.items():
        table_data.append([sensor, f"{stats['Max']:.2f}", f"{stats['Min']:.2f}", f"{stats['Mean']:.2f}"])
    stats_table = Table(table_data, colWidths=[150, 100, 100, 100])
    stats_table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ])
    stats_table.setStyle(stats_table_style)
    elements.append(stats_table)
    elements.append(Spacer(1, 0.2 * inch))
    
    # 새 페이지 추가 (검증 결과 섹션 전환)
    elements.append(PageBreak())
    
    # 검증 결과 섹션
    title = Paragraph("<b>3. Validation Results</b>", heading_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))

    acceptable_range_text = Paragraph(
        f"Acceptable range: <b>{acceptable_lower_bound:.2f}</b> ~ <b>{acceptable_upper_bound:.2f}</b>",
        styles["Normal"]
    )
    elements.append(acceptable_range_text)
    elements.append(Spacer(1, 0.2 * inch))

    table_data = [["Sensor", "Mean Difference", "Status"]]
    for sensor, result in validation_results.items():
        status = "Within range" if result["within_acceptable_range"] else "Out of range"
        table_data.append([sensor, f"{result['mean_difference']:.2f}", status])
    validation_table = Table(table_data, colWidths=[150, 100, 100])
    validation_table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ])
    # 상태 열의 텍스트 색상을 동적으로 설정
    for row_idx, row in enumerate(table_data[1:], start=1):
        status = row[2]
        if status == "Within range":
            validation_table_style.add("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.green)
        elif status == "Out of range":
            validation_table_style.add("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.red)
    validation_table.setStyle(validation_table_style)
    elements.append(validation_table)

    # 그래프 이미지 추가 (존재하는 경우)
    if graph_path and os.path.exists(graph_path):
        graph_img = Image(graph_path, width=550, height=250)
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(graph_img)
    
    if time_graph and os.path.exists(time_graph):
        time_graph_img = Image(time_graph, width=456, height=636)
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(time_graph_img)

    pdf.build(elements)
    log(f"PDF report saved: {output_filename}")
    return output_filename
