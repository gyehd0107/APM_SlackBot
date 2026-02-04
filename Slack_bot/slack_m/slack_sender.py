import os

from Slack_bot.log_m.log import log
from Slack_bot.slack_m.slack_env import client, SLACK_CHANNEL_ID, SLACK_ISSUE_CHANNEL_ID
from Slack_bot.models import lists


def send_validation_results_to_slack(
    validation_results,
    acceptable_lower_bound,
    acceptable_upper_bound,
    cra,
    crb,
    report_type,
):
    report_type = (
        "Daily Report"
        if report_type == "Daily"
        else "Weekly Report"
        if report_type == "Weekly"
        else "Monthly Report"
    )

    validation_blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{report_type} ({cra} ~ {crb})"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"Acceptable range: *{acceptable_lower_bound:.2f} "
                    f"~ {acceptable_upper_bound:.2f}*"
                ),
            },
        },
        {"type": "divider"},
    ]

    for sensor, result in validation_results.items():
        status_emoji = ":white_check_mark:" if result["within_acceptable_range"] else ":x:"
        validation_blocks.append(
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Sensor*: `{sensor}`"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Mean Difference*: `{result['mean_difference']:.2f}` {status_emoji}",
                    },
                ],
            }
        )
        validation_blocks.append({"type": "divider"})

    try:
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text=f"{report_type} ({cra} ~ {crb})",
            blocks=validation_blocks,
        )
        if response["ok"]:
            log(f"{report_type} successfully sent to Slack.")
        else:
            log(f"Failed to send {report_type}: {response['error']}")
    except Exception as exc:
        log(f"Error sending {report_type} to Slack: {exc}")


def _build_incident_blocks(incident: lists, header_text):
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_text,
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Service:*\n {incident.get_service()}"},
                {"type": "mrkdwn", "text": f"*Occurred:*\n {incident.get_occurred_at()}"},
                {"type": "mrkdwn", "text": f"*Restored:*\n {incident.get_restored_at()}"},
                {"type": "mrkdwn", "text": f"*Detail:*\n {incident.get_detail()}"},
                {"type": "mrkdwn", "text": f"*Status:*\n {incident.get_status()}"},
            ],
        },
    ]


def restored_blocks(incident: lists):
    blocks = _build_incident_blocks(
        incident, f":white_check_mark: list #{incident.get_id()}"
    )
    try:
        result = client.chat_postMessage(
            channel=SLACK_ISSUE_CHANNEL_ID,
            text=f":white_check_mark: list #{incident.get_id()} - {incident.get_service()} 복구",
            blocks=blocks,
        )
        print(result)
    except Exception as exc:
        print(f"Error posting message: {exc}")


def default_blocks(incident: lists):
    blocks = _build_incident_blocks(incident, f":warning: list #{incident.get_id()}")
    try:
        result = client.chat_postMessage(
            channel=SLACK_ISSUE_CHANNEL_ID,
            text=f":warning: list #{incident.get_id()} - {incident.get_service()} 발생",
            blocks=blocks,
        )
        print(result)
    except Exception as exc:
        print(f"Error posting message: {exc}")


def send_plot_to_slack(pdf_file_path, plot_file_path, cra, crb, report_type):
    try:
        if not os.path.exists(plot_file_path):
            log(f"Error: Plot file not found: {plot_file_path}")
            return

        plot_response = client.files_upload_v2(
            channel=SLACK_CHANNEL_ID,
            file=plot_file_path,
            initial_comment=f"{report_type} Report_ graph({cra} ~ {crb})",
        )

        if plot_response["ok"]:
            log(f"Plot file {os.path.basename(plot_file_path)} successfully sent to Slack.")
        else:
            log(f"Slack upload failed for plot file: {plot_response['error']}")
            return

        if not os.path.exists(pdf_file_path):
            log(f"Error: PDF file not found: {pdf_file_path}")
            return

        pdf_response = client.files_upload_v2(
            channel=SLACK_CHANNEL_ID,
            file=pdf_file_path,
            initial_comment=f"{report_type} Report_pdf({cra} ~ {crb})",
        )

        if pdf_response["ok"]:
            log(f"PDF file {os.path.basename(pdf_file_path)} successfully sent to Slack.")
        else:
            log(f"Slack upload failed for PDF file: {pdf_response['error']}")
    except Exception as exc:
        log(f"Error sending files to Slack: {exc}")


def send_nan_alert_to_slack(cra, crb, error_data):
    start_datetime = cra.strftime("%Y-%m-%d %H:%M:%S%z")
    end_datetime = crb.strftime("%Y-%m-%d %H:%M:%S%z")
    start_datetime = f"{start_datetime[:-5]}{start_datetime[-5:-2]}:{start_datetime[-2:]}"
    end_datetime = f"{end_datetime[:-5]}{end_datetime[-5:-2]}:{end_datetime[-2:]}"

    header = "[DATA Quality Alert] NaN Detected"
    period = f"({start_datetime} ~ {end_datetime})"

    try:
        if not error_data:
            header_text = f"{header} 🟢"
            message = f"{header_text}\n{period}\n\nNo NaN (Not a Number) detected"
            response = client.chat_postMessage(
                channel=SLACK_CHANNEL_ID,
                text=header_text,
                blocks=[
                    {"type": "section", "text": {"type": "mrkdwn", "text": message}}
                ],
            )
        else:
            header_text = f"{header} 🔴"
            alert_text = "NaN (Not a Number) detected"
            rows = [
                [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "text",
                                        "text": "Column",
                                        "style": {"bold": True},
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "text",
                                        "text": "NaN Count",
                                        "style": {"bold": True},
                                    }
                                ],
                            }
                        ],
                    },
                ]
            ]
            total_nan = 0
            for column, nan_rows in error_data:
                count = len(nan_rows)
                if count == 0:
                    continue
                total_nan += count
                rows.append(
                    [
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [{"type": "text", "text": column}],
                                }
                            ],
                        },
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [
                                        {
                                            "type": "text",
                                            "text": f"{count:,}",
                                            "style": {"bold": True},
                                        }
                                    ],
                                }
                            ],
                        },
                    ]
                )

            response = client.chat_postMessage(
                channel=SLACK_CHANNEL_ID,
                text=header_text,
                blocks=[
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": header_text},
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*{period}*"},
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": alert_text,
                        },
                    },
                ],
                attachments=[
                    {
                        "blocks": [
                            {
                                "type": "table",
                                "column_settings": [
                                    {"is_wrapped": True},
                                    {"align": "right"},
                                ],
                                "rows": rows,
                            }
                        ]
                    }
                ],
            )
        if response["ok"]:
            log("NaN alert successfully sent to Slack.")
        else:
            log(f"Failed to send NaN alert: {response['error']}")
    except Exception as exc:
        log(f"Error sending NaN alert to Slack: {exc}")
