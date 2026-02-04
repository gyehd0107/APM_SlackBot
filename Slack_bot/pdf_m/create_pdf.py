import os
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from Slack_bot.log_m.log import log

REPORT_TITLES = {
    "Daily": "Daily Report",
    "Weekly": "Weekly Report",
    "Monthly": "Monthly Report",
}

PALETTE = {
    "primary": colors.HexColor("#2F5B9A"),
    "secondary": colors.HexColor("#3E6FB3"),
    "accent": colors.HexColor("#3E6FB3"),
    "header_bg": colors.HexColor("#2F5B9A"),
    "row_even": colors.HexColor("#F7F9FC"),
    "row_odd": colors.HexColor("#FFFFFF"),
    "border": colors.HexColor("#D0D7DE"),
    "ok": colors.HexColor("#1A7F37"),
    "warn": colors.HexColor("#B54708"),
}


def _format_dt(value):
    if pd.isna(value):
        return "-"
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _summarize_nan_intervals(nan_rows):
    if nan_rows is None or nan_rows.empty:
        return []

    time_col = "APMdatetime"
    if time_col not in nan_rows.columns:
        time_col = "RPMdatetime"

    rows = nan_rows[[time_col]].copy()
    rows[time_col] = pd.to_datetime(rows[time_col], errors="coerce")
    rows = rows.dropna(subset=[time_col]).sort_values(time_col)
    if rows.empty:
        return []

    diffs = rows[time_col].diff().dropna()
    positive_diffs = diffs[diffs > pd.Timedelta(0)]
    base_gap = positive_diffs.median() if not positive_diffs.empty else pd.Timedelta(minutes=1)
    gap_threshold = base_gap * 1.5

    intervals = []
    start = rows[time_col].iloc[0]
    prev = start
    count = 1
    for current in rows[time_col].iloc[1:]:
        if current - prev <= gap_threshold:
            count += 1
        else:
            intervals.append((start, prev, count))
            start = current
            count = 1
        prev = current
    intervals.append((start, prev, count))
    return intervals


def _modern_table_style():
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), PALETTE["header_bg"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
            ("TOPPADDING", (0, 0), (-1, 0), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, PALETTE["border"]),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PALETTE["row_even"], PALETTE["row_odd"]]),
        ]
    )


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
    pm_statistics,
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

    main_title = REPORT_TITLES.get(report_type, "Monthly Report")
    pdf = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=1,
        fontName="Helvetica-Bold",
        textColor=colors.black,
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontSize=13,
        leading=16,
        alignment=1,
        fontName="Helvetica",
        textColor=colors.black,
    )
    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        fontName="Helvetica-Bold",
        textColor=colors.black,
        spaceBefore=4,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        fontName="Helvetica",
        textColor=colors.black,
    )
    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        fontName="Helvetica",
        textColor=colors.black,
    )

    elements = []

    title_table = Table(
        [[Paragraph(f"<b>{main_title}</b>", title_style)], [Paragraph(f"{cra_formatted} ~ {crb_formatted}", subtitle_style)]],
        colWidths=[6.8 * inch],
    )
    title_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("LINEBELOW", (0, -1), (-1, -1), 1, PALETTE["border"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(title_table)
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph(f"<b>1. {report_type} Data Collection Summary</b>", section_style))
    elements.append(Spacer(1, 0.1 * inch))

    summary_cards = [
        ["Collection Duration", f"{time_difference} ({total_hours:.0f} min)"],
        ["Total Data Cells", f"{int(total_cells):,}"],
        ["NaN Cells", f"{int(nan_cells):,}"],
    ]
    summary_table = Table(summary_cards, colWidths=[2.1 * inch, 4.7 * inch], rowHeights=[0.35 * inch] * 3)
    summary_table.hAlign = "LEFT"
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), PALETTE["secondary"]),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.whitesmoke),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.black),
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F5F7FA")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, PALETTE["border"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("<b>2. NaN Interval Summary</b>", section_style))
    elements.append(Spacer(1, 0.08 * inch))

    if error_data:
        for column, nan_rows in error_data:
            intervals = _summarize_nan_intervals(nan_rows)
            elements.append(
                Paragraph(f"<b>{column}</b> <font color='#57606A'>({len(nan_rows):,} NaN)</font>", label_style)
            )
            table_data = [["NaN Interval Start", "NaN Interval End", "Count"]]
            if intervals:
                for start_dt, end_dt, count in intervals:
                    table_data.append([_format_dt(start_dt), _format_dt(end_dt), f"{count:,}"])
            else:
                table_data.append(["-", "-", "0"])

            error_table = Table(table_data, colWidths=[2.25 * inch, 2.25 * inch, 1.2 * inch])
            error_table.hAlign = "LEFT"
            error_table.setStyle(_modern_table_style())
            elements.append(error_table)
            elements.append(Spacer(1, 0.12 * inch))
    else:
        no_nan_table = Table([["No NaN interval detected in this report range."]], colWidths=[6.8 * inch])
        no_nan_table.hAlign = "LEFT"
        no_nan_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E7F5EC")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("BOX", (0, 0), (-1, -1), 0.5, PALETTE["border"]),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(no_nan_table)

    elements.append(Spacer(1, 0.18 * inch))
    elements.append(Paragraph("<b>3. PM Statistics</b>", section_style))
    elements.append(Spacer(1, 0.08 * inch))

    stats_data = [["Sensor", "Max", "Min", "Mean"]]
    for sensor, stats in pm_statistics.items():
        stats_data.append([sensor, f"{stats['Max']:.2f}", f"{stats['Min']:.2f}", f"{stats['Mean']:.2f}"])

    stats_table = Table(stats_data, colWidths=[2.1 * inch, 1.55 * inch, 1.55 * inch, 1.6 * inch])
    stats_table.hAlign = "LEFT"
    stats_table.setStyle(_modern_table_style())
    elements.append(stats_table)

    elements.append(PageBreak())
    elements.append(Paragraph("<b>4. Validation Results</b>", section_style))
    elements.append(
        Paragraph(
            f"Acceptable range: <b>{acceptable_lower_bound:.2f}</b> ~ <b>{acceptable_upper_bound:.2f}</b>",
            body_style,
        )
    )
    elements.append(Spacer(1, 0.1 * inch))

    validation_data = [["Sensor", "Mean Difference", "Status"]]
    for sensor, result in validation_results.items():
        status = "Within range" if result["within_acceptable_range"] else "Out of range"
        validation_data.append([sensor, f"{result['mean_difference']:.2f}", status])

    validation_table = Table(validation_data, colWidths=[2.2 * inch, 2.1 * inch, 2.5 * inch])
    validation_table.hAlign = "LEFT"
    validation_style = _modern_table_style()
    for row_idx, row in enumerate(validation_data[1:], start=1):
        if row[2] == "Within range":
            validation_style.add("BACKGROUND", (2, row_idx), (2, row_idx), colors.HexColor("#E7F5EC"))
            validation_style.add("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.black)
        else:
            validation_style.add("BACKGROUND", (2, row_idx), (2, row_idx), colors.HexColor("#FFF4E5"))
            validation_style.add("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.black)
        validation_style.add("FONTNAME", (2, row_idx), (2, row_idx), "Helvetica-Bold")
    validation_table.setStyle(validation_style)
    elements.append(validation_table)
    elements.append(Spacer(1, 0.18 * inch))

    if graph_path and os.path.exists(graph_path):
        elements.append(Paragraph("<b>Validation Distribution Chart</b>", label_style))
        elements.append(Spacer(1, 0.05 * inch))
        elements.append(Image(graph_path, width=6.8 * inch, height=2.9 * inch))
        elements.append(Spacer(1, 0.12 * inch))

    if time_graph and os.path.exists(time_graph):
        elements.append(Paragraph("<b>Sensor Trend Chart</b>", label_style))
        elements.append(Spacer(1, 0.05 * inch))
        elements.append(Image(time_graph, width=6.4 * inch, height=8.0 * inch))

    pdf.build(elements)
    log(f"PDF report saved: {output_filename}")
    return output_filename
