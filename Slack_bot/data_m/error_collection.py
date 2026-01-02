import pandas as pd

from Slack_bot.data_m.constants import COLUMNS


def error_collection(data, columns=None):
    if columns is None:
        columns = COLUMNS
    error_data = []
    for column in columns:
        if column not in ["APMdatetime", "RPMdatetime"]:
            data[column] = pd.to_numeric(data[column], errors="coerce")
            nan_rows = data[data[column].isna()]
            if not nan_rows.empty:
                error_data.append(
                    (column, nan_rows[["APMdatetime", "RPMdatetime", column]])
                )
    return data, error_data
