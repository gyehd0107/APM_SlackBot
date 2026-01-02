from datetime import datetime
import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm
from Slack_bot.log_m.log import log


def plot_sensor_differences(
    data,
    sensor_columns,
    acceptable_lower_bound,
    acceptable_upper_bound,
    cra,
    crb,
    report_type,
):
    """
    주어진 데이터에 대해 센서 별 차이값의 분포를 히스토그램과 정규분포 커브로 그려,
    허용 가능한 범위와 평균을 함께 표시한 후, 결과 그래프를 파일로 저장하는 함수입니다.
    
    Parameters:
        data (DataFrame): 전처리된 데이터
        sensor_columns (list): 센서 컬럼 목록 (예: ['pm_1_1', 'pm_1_2', ...])
        acceptable_lower_bound (float): 허용 가능한 하한값
        acceptable_upper_bound (float): 허용 가능한 상한값
        cra (datetime 또는 str): 시작 시각
        crb (datetime 또는 str): 종료 시각
        report_type (str): 보고서 유형(예: "Weekly")
    
    Returns:
        str: 저장된 그래프 파일의 경로
    """
    # cra와 crb를 문자열로 변환
    cra_str = cra.strftime("%Y%m%dT%H%M%S") if isinstance(cra, datetime) else cra
    crb_str = crb.strftime("%Y%m%dT%H%M%S") if isinstance(crb, datetime) else crb

    global_min = data[[f"{sensor}_diff" for sensor in sensor_columns]].min().min()
    global_max = data[[f"{sensor}_diff" for sensor in sensor_columns]].max().max()

    # 각 센서의 히스토그램 밀도 중 최댓값을 기준으로 y축 상한을 결정
    global_max_density = 0
    for sensor in sensor_columns:
        hist_values, _ = np.histogram(
            data[f"{sensor}_diff"], bins=20, range=(global_min, global_max), density=True
        )
        global_max_density = max(global_max_density, hist_values.max())

    plt.figure(figsize=(15, 10))
    for i, sensor in enumerate(sensor_columns, 1):
        sensor_mean = data[f"{sensor}_diff"].mean()
        sensor_std = data[f"{sensor}_diff"].std()

        plt.subplot(3, 3, i)
        plt.hist(
            data[f"{sensor}_diff"],
            bins=20,
            color="skyblue",
            edgecolor="black",
            alpha=0.7,
            density=True,
            range=(global_min, global_max),
        )
        x_values = np.linspace(global_min, global_max, 100)
        y_values = norm.pdf(x_values, sensor_mean, sensor_std)
        plt.plot(
            x_values,
            y_values,
            color="purple",
            linestyle="-",
            linewidth=2,
            label="Normal Distribution",
        )

        if acceptable_lower_bound is not None:
            plt.axvline(
                acceptable_lower_bound,
                color="red",
                linestyle="--",
                label=f"Acceptable Lower ({acceptable_lower_bound:.2f})",
            )
        if acceptable_upper_bound is not None:
            plt.axvline(
                acceptable_upper_bound,
                color="green",
                linestyle="--",
                label=f"Acceptable Upper ({acceptable_upper_bound:.2f})",
            )
        plt.axvline(
            sensor_mean,
            color="blue",
            linestyle="-",
            label=f"Mean Diff ({sensor_mean:.2f})",
        )

        plt.title(f"Distribution of Differences for {sensor}")
        plt.xlabel("Difference (Sensor - Reference)")
        plt.ylabel("Density")
        plt.legend()
        plt.ylim(0, global_max_density * 1.5)

    # 날짜 문자열을 읽기 쉬운 형식으로 변환
    cra_formatted = datetime.strptime(cra_str, "%Y%m%dT%H%M%S").strftime("%Y-%m-%d %H:%M")
    crb_formatted = datetime.strptime(crb_str, "%Y%m%dT%H%M%S").strftime("%Y-%m-%d %H:%M")

    year = cra_str[:4]
    month = cra_str[4:6]
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
            "Validation_Result",
        )
    )
    os.makedirs(base_path, exist_ok=True)

    output_filename = os.path.join(
        base_path,
        f"{cra_formatted.replace(':', '_')}~{crb_formatted.replace(':', '_')}_validation.png",
    )
    plt.suptitle(f"{cra_formatted} ~ {crb_formatted}", fontsize=16)
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.close()
    log(f"Plot saved to {output_filename}")
    return output_filename
