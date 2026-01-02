from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz
from Slack_bot.data_m.constants import SENSOR_COLUMNS
from Slack_bot.data_m.process_validate import process_validate
from Slack_bot.plot_m.plot_sensor import plot_sensor_differences
from Slack_bot.plot_m.plot_trends import plot_trends_series
from Slack_bot.pdf_m.create_pdf import save_report_pdf
from Slack_bot.slack_m.slack_sender import (
    send_plot_to_slack,
    send_validation_results_to_slack,
)
from Slack_bot.log_m.log import log

KST = pytz.timezone("Asia/Seoul")


def _resolve_report_range(days_offset, months_offset):
    now = datetime.now(KST)
    if months_offset is not None:
        cra = (now - relativedelta(months=months_offset)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    else:
        cra = (now - timedelta(days=days_offset)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    crb = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return cra, crb


def send_report(report_type, days_offset=None, months_offset=None):
    cra, crb = _resolve_report_range(days_offset, months_offset)
    cra_str = cra.strftime("%Y%m%dT%H%M%S")
    crb_str = crb.strftime("%Y%m%dT%H%M%S")

    log(f"Generating {report_type} report for {cra_str} ~ {crb_str}")

    # 데이터 처리
    (
        data,
        validation_results,
        acceptable_lower_bound,
        acceptable_upper_bound,
        time_difference,
        total_hours,
        total_cells,
        nan_cells,
        error_data,
        statistics,
    ) = process_validate(cra_str, crb_str, report_type)
    if data is None or data.empty:
        log(f"No data found for {report_type} range: CRA={cra_str}, CRB={crb_str}")
        return

    # 그래프 생성
    graph_path = plot_sensor_differences(
        data,
        SENSOR_COLUMNS,
        acceptable_lower_bound,
        acceptable_upper_bound,
        cra,
        crb,
        report_type,
    )
    time_graph = plot_trends_series(data, SENSOR_COLUMNS, cra, crb, report_type)

    # PDF 보고서 생성
    pdf_path = save_report_pdf(
        graph_path,
        validation_results,
        acceptable_lower_bound,
        acceptable_upper_bound,
        cra_str,
        crb_str,
        report_type,
        time_difference,
        total_hours,
        total_cells,
        nan_cells,
        error_data,
        time_graph,
        statistics,
    )

    # Slack 전송
    send_validation_results_to_slack(
        validation_results,
        acceptable_lower_bound,
        acceptable_upper_bound,
        cra,
        crb,
        report_type,
    )
    send_plot_to_slack(pdf_path, graph_path, cra, crb, report_type)
