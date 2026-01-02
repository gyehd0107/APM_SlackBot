import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from Slack_bot.log_m.log import log


def plot_trends_series(data, sensor_columns, cra, crb, report_type):
    """
    주어진 데이터에 대해 센서 값의 시계열 변화를 그린 그래프를 생성하고 파일로 저장하는 함수입니다.
    
    Parameters:
        data (DataFrame): 전처리된 데이터
        sensor_columns (list): 시계열에 포함할 센서 컬럼 목록 (예: ['pm_1_1', 'pm_1_2', ...])
        cra (datetime 또는 str): 시작 시각
        crb (datetime 또는 str): 종료 시각
        report_type (str): 보고서 유형(예: "Weekly")
    
    Returns:
        str: 저장된 트렌드 그래프 파일의 경로
    """
    # 원본 리스트를 변경하지 않도록 복사 후, 기준 컬럼 추가
    sensor_columns = sensor_columns.copy()
    sensor_columns.append("reference_pm_after")

    num_features = len(sensor_columns)
    fig, axes = plt.subplots(num_features, 1, figsize=(10, 1.8 * num_features), sharex=True)

    data["APMdatetime"] = pd.to_datetime(data["APMdatetime"], errors="coerce")
    global_max = data[sensor_columns].max().max()

    for i, sensor in enumerate(sensor_columns):
        sensor_data = data[["APMdatetime", sensor]].dropna()
        prev_idx = 0
        for idx in range(1, len(sensor_data)):
            if (
                sensor_data["APMdatetime"].iloc[idx]
                - sensor_data["APMdatetime"].iloc[idx - 1]
            ).total_seconds() > 3600:
                axes[i].plot(
                    sensor_data["APMdatetime"].iloc[prev_idx:idx],
                    sensor_data[sensor].iloc[prev_idx:idx],
                    color="b",
                    linewidth=1,
                )
                prev_idx = idx
        axes[i].plot(
            sensor_data["APMdatetime"].iloc[prev_idx:],
            sensor_data[sensor].iloc[prev_idx:],
            color="b",
            linewidth=1,
        )
        axes[i].set_ylabel(sensor, fontsize=8)
        axes[i].tick_params(axis="both", labelsize=7)
        axes[i].grid(True, linestyle="--", alpha=0.7)
        axes[i].set_ylim(0, global_max)

    fig.suptitle("Time Series Plots of Sensors (Hourly)", fontsize=10, y=0.95)
    fig.text(0.5, 0.0, "Time (APMdatetime)", ha="center", fontsize=9)
    fig.text(0.0, 0.5, "Sensor Values", va="center", rotation="vertical", fontsize=9)
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3, top=0.9)

    cra_str = cra.strftime("%Y%m%dT%H%M%S") if isinstance(cra, datetime) else cra
    crb_str = crb.strftime("%Y%m%dT%H%M%S") if isinstance(crb, datetime) else crb
    year = cra_str[:4]
    month = crb_str[4:6]
    base_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "save",
            "graph",
            year,
            month,
            report_type,
            "Trend",
        )
    )
    os.makedirs(base_path, exist_ok=True)
    output_filename = os.path.join(base_path, f"{cra_str}_{crb_str}_trend.png")
    plt.savefig(output_filename)
    plt.close()
    log(f"Plot saved to {output_filename}")
    return output_filename
