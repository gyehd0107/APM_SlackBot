from datetime import datetime, timedelta
import os

import requests
from dotenv import load_dotenv

from Slack_bot.log_m.log import log

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(ENV_PATH)

BASE_URL = os.getenv(
    "DATA_BASE_URL", "http://114.71.220.59:2021/Mobius/Ksensor_ubicomp_2/data"
)
HEADERS = {
    "Accept": "application/json",
    "X-M2M-RI": os.getenv("M2M_RI", "sdaf343545"),
    "X-M2M-Origin": os.getenv("M2M_ORIGIN", "S20170717074825768bp2l"),
}


def fetch_data_interval(cra_str, next_cra_str, base_url, headers):
    url = f"{base_url}?cra={cra_str}&crb={next_cra_str}&ty=4&rcn=4&lim=2000"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        log(
            f"[ERROR] Failed to fetch data for {cra_str} to {next_cra_str}. "
            f"HTTP {response.status_code}"
        )
        return []

    rsp_data = response.json().get("m2m:rsp", {}).get("m2m:cin", [])
    if not rsp_data:
        log(f"[INFO] No data found for {cra_str} to {next_cra_str}.")
        return []

    daily_data = []
    for cin in rsp_data:
        con_value = cin.get("con")

        try:
            if isinstance(con_value, str):
                row = [item.strip() for item in con_value.split(",")]  # 怨듬갚 ?쒓굅 ?ы븿
                daily_data.append(row)
            else:
                log(
                    f"[WARNING] 'con' is not a string: {con_value} "
                    f"(type: {type(con_value)})"
                )
        except Exception as e:
            log(f"[ERROR] Exception while processing 'con': {con_value}, error: {e}")

    log(f"[INFO] Fetched {len(daily_data)} records for {cra_str} to {next_cra_str}.")
    return daily_data


def fetch_all_data(cra, crb):
    all_data = []

    current_cra = datetime.strptime(cra, "%Y%m%dT%H%M%S")
    end_crb = datetime.strptime(crb, "%Y%m%dT%H%M%S")

    while current_cra < end_crb:
        next_cra = current_cra + timedelta(days=1)
        cra_str = current_cra.strftime("%Y%m%dT%H%M%S")
        next_cra_str = next_cra.strftime("%Y%m%dT%H%M%S")

        daily_data = fetch_data_interval(cra_str, next_cra_str, BASE_URL, HEADERS)
        all_data.extend(daily_data)
        current_cra = next_cra

    return all_data

