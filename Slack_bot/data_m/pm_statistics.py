# PM 센서별 통계 계산
def pm_statistics(data, sensor_columns):
    statistics = {}
    for sensor in sensor_columns:
        max_value = data[sensor].max()
        min_value = data[sensor].min()
        mean_value = data[sensor].mean()
        statistics[sensor] = {
            "Max": max_value,
            "Min": min_value,
            "Mean": mean_value,
        }
    return statistics
