import pandas as pd
from scipy.stats import norm
from Slack_bot.data_m.constants import REFERENCE_COLUMN, SENSOR_COLUMNS


def sensor_validation(data):
    """
    센서 데이터와 기준(reference_pm_after)을 이용해 차이를 계산하고,
    전체 통계 기반의 검증 결과(신뢰구간 내 포함 여부 등)를 반환하는 함수.
    """
    # 센서별 차이 계산
    for sensor in SENSOR_COLUMNS:
        data[f"{sensor}_diff"] = data[sensor] - data[REFERENCE_COLUMN]
    
    # 모든 센서의 차이를 하나의 Series로 합침
    all_differences = pd.concat([data[f"{sensor}_diff"] for sensor in SENSOR_COLUMNS])
    
    # 통계치 계산 및 신뢰구간 산출 (95% 신뢰수준)
    global_mean = all_differences.mean()
    global_std = all_differences.std()
    confidence_level = 0.95
    z_value = norm.ppf((1 + confidence_level) / 2)
    acceptable_lower_bound = global_mean - (z_value * global_std)
    acceptable_upper_bound = global_mean + (z_value * global_std)
    
    # 각 센서별 검증 결과 생성
    validation_results = {}
    for sensor in SENSOR_COLUMNS:
        sensor_mean_diff = data[f"{sensor}_diff"].mean()
        is_within_range = (
            acceptable_lower_bound <= sensor_mean_diff <= acceptable_upper_bound
        )
        validation_results[sensor] = {
            "mean_difference": sensor_mean_diff,
            "within_acceptable_range": is_within_range,
        }
    
    return validation_results, acceptable_lower_bound, acceptable_upper_bound
