from datetime import datetime

from Slack_bot.data_m.constants import COLUMNS, SENSOR_COLUMNS
from Slack_bot.data_m.create_df import create_dataframe
from Slack_bot.data_m.error_collection import error_collection
from Slack_bot.data_m.fetch_data import fetch_all_data
from Slack_bot.data_m.pm_statistics import pm_statistics
from Slack_bot.data_m.sensor_validation import sensor_validation


def process_validate(cra, crb, report_type):
    """
    전체 데이터 처리 파이프라인:
      1. 데이터 수집
      2. DataFrame 생성 및 정렬
      3. 숫자형 변환 및 오류 데이터 수집
      4. 결측치 보간
      5. 센서 검증 및 통계 계산
      6. CSV 파일로 저장
    """
    # 1. 데이터 수집
    all_data = fetch_all_data(cra, crb)
    
    # 2. DataFrame 생성
    data = create_dataframe(all_data)
    
    # 3. 데이터 숫자형 변환 및 에러 데이터 수집
    data, error_data = error_collection(data, COLUMNS)
    
    # 4. 전체 셀 수 및 NAN 셀 수 (처리 전)
    total_cells = data.size / len(COLUMNS)
    nan_cells = data.isnull().sum().sum()
    
    # 결측치 보간: forward fill 후 backward fill
    data = data.ffill().bfill()
    
    # 5. 센서 검증 결과 계산
    validation_results, acceptable_lower_bound, acceptable_upper_bound = sensor_validation(data)
    
    # 시간 차 계산
    start_datetime = datetime.strptime(cra, "%Y%m%dT%H%M%S")
    end_datetime = datetime.strptime(crb, "%Y%m%dT%H%M%S")
    time_difference = end_datetime - start_datetime
    total_hours = time_difference.total_seconds() / 60  # 초 -> 분 변환

    statistics = pm_statistics(data, SENSOR_COLUMNS)

    return (
        data,
        validation_results,
        acceptable_lower_bound,
        acceptable_upper_bound,
        time_difference,
        total_hours,
        total_cells,
        nan_cells,
        error_data,
        statistics
    )
