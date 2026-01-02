import pandas as pd

from Slack_bot.data_m.constants import COLUMNS


def create_dataframe(all_data):
    data = pd.DataFrame(all_data, columns=COLUMNS)
    data = data.sort_values(
        by="APMdatetime", key=lambda col: pd.to_datetime(col, errors="coerce")
    ).reset_index(drop=True)
    return data
