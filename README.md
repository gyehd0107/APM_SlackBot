# Slack Bot 리포트 + Incident 리스너

센서 데이터의 검증 리포트(일간/주간/월간)를 생성해 Slack으로 전송하고, WebSocket으로 들어오는 장애(incident) 이벤트를 Slack 채널로 전달합니다. 데이터 수집부터 통계/검증, 그래프/리포트 생성, Slack 전송까지 하나의 파이프라인으로 구성되어 있습니다.

## 기능 개요
- HTTP API에서 센서 데이터를 수집합니다.
- 기준(reference)과의 차이를 계산해 검증 결과를 산출합니다.
- 그래프와 PDF 리포트를 생성합니다.
- Slack 채널로 요약/파일을 전송합니다.
- WebSocket으로 전달되는 incident 업데이트를 감지해 Slack으로 알립니다.

## 요구 사항
- Python 3.11+ 권장
- Slack 봇 토큰 및 채널 ID
- 데이터 API, WebSocket 서버 접근 가능한 네트워크

## 설치
프로젝트에서 사용하는 패키지를 한 번에 설치합니다.

```bash
pip install -r install.txt
```

## 가상환경(venv)
GitHub에는 `venv/`를 올리지 않습니다. 로컬에서 생성 후 설치하세요.

```bash
python -m venv venv
venv\Scripts\activate
pip install -r install.txt
```

## 환경 설정
`./.env` 파일을 생성하고 아래 값을 설정합니다.

```
SLACK_BOT_TOKEN=...
SLACK_CHANNEL_ID=...
SLACK_ISSUE_CHANNEL_ID=...
```

선택값:
- `BOT_LOG_DIR`: 로그 디렉터리 경로(기본값 `/home/Ubicomp/bot/total_log`, 실패 시 `./total_log`로 대체)

## 실행 방법
### 스케줄러(리포트 전송)
일간/주간/월간 리포트를 스케줄에 따라 전송합니다.

```bash
python start.py
```

### Incident 리스너
WebSocket으로 들어오는 incident 이벤트를 Slack으로 전송합니다.

```bash
python incident_bot.py
```

## 출력 경로
- 그래프: `save/graph/<YYYY>/<MM>/<ReportType>/...`
- PDF: `save/report_pdf/<YYYY>/<MM>/<ReportType>/...`
- 로그: `total_log/` (또는 `BOT_LOG_DIR`)

## 주요 파일 및 역할 (구체 설명)
아래는 프로젝트에서 실제 동작에 필요한 파일들 기준입니다. `venv/`, `save/`, `__pycache__/`는 런타임 생성물이라 문서에서 제외했습니다.

### 실행 엔트리
- `start.py`
  - 스케줄러 엔트리 포인트입니다.
  - `schedule` 라이브러리로 일간/주간/월간 리포트 전송 시간을 설정합니다.
  - `Slack_bot.send_m.send_report.send_report`를 호출해 리포트를 생성/전송합니다.
  - 실행 로그는 `Slack_bot.utils.logging.write_log`로 기록합니다.
- `incident_bot.py`
  - WebSocket 기반 incident 리스너입니다.
  - `WEBSOCKET_URI`로 연결해 메시지를 수신합니다.
  - 메시지를 파싱해 `Slack_bot.models.lists` 형태로 변환합니다.
  - 상태가 `restored`면 복구 메시지, 아니면 발생 메시지를 Slack으로 전송합니다.

### Slack 관련
- `Slack_bot/slack_m/slack_env.py`
  - `.env`에서 Slack 토큰과 채널 ID를 읽어옵니다.
  - `slack_sdk.WebClient`를 생성해 API 호출에 사용합니다.
- `Slack_bot/slack_m/slack_sender.py`
  - 리포트 결과와 파일을 Slack으로 전송합니다.
  - `send_validation_results_to_slack`: 센서별 검증 결과를 Block 메시지로 전송합니다.
  - `send_plot_to_slack`: 그래프/리포트 PDF 파일을 업로드합니다.
  - `default_blocks`, `restored_blocks`: incident 발생/복구 메시지 포맷을 생성해 전송합니다.

### 데이터 수집/전처리
- `Slack_bot/data_m/fetch_data.py`
  - HTTP API에서 센서 데이터를 가져옵니다.
  - `BASE_URL`과 `HEADERS`를 사용해 날짜 구간 단위로 데이터를 수집합니다.
  - 응답의 `m2m:cin`을 파싱해 CSV 형태의 리스트로 변환합니다.
- `Slack_bot/data_m/create_df.py`
  - 수집한 리스트를 pandas DataFrame으로 변환합니다.
  - 컬럼 정렬/형식 맞춤 역할을 수행합니다.
- `Slack_bot/data_m/constants.py`
  - 데이터 컬럼 정의 및 센서 컬럼 목록을 관리합니다.
  - `SENSOR_COLUMNS`, `REFERENCE_COLUMN`, `COLUMNS`를 제공합니다.
- `Slack_bot/data_m/error_collection.py`
  - 숫자형 변환을 수행하고, 변환 실패(NaN) 행을 수집합니다.
  - 오류 데이터는 보고서에 포함됩니다.
- `Slack_bot/data_m/process_validate.py`
  - 전체 파이프라인을 묶는 핵심 함수입니다.
  - 수집 → DataFrame → 숫자형 변환 → 보간 → 검증 → 통계 계산을 수행합니다.
  - 리포트 생성에 필요한 데이터(검증 결과, 통계, 오류 목록 등)를 반환합니다.
- `Slack_bot/data_m/sensor_validation.py`
  - 기준(reference) 대비 센서 차이를 계산합니다.
  - 전체 센서 차이의 평균/표준편차로 신뢰구간(95%)을 계산하고,
    센서별 평균 차이가 범위 내인지 판단합니다.
- `Slack_bot/data_m/pm_statistics.py`
  - 센서별 통계(최대/최소/평균)를 계산해 PDF 리포트에 넣습니다.

### 그래프 생성
- `Slack_bot/plot_m/plot_sensor.py`
  - 센서 차이 분포 히스토그램과 정규분포 곡선을 그립니다.
  - 허용 범위(상/하한)와 평균선을 표시합니다.
  - 저장 위치는 `save/graph/.../Validation_Result/`입니다.
- `Slack_bot/plot_m/plot_trends.py`
  - 센서 시계열 그래프를 생성합니다.
  - 데이터 간격이 1시간 이상 벌어질 경우 구간을 끊어 표시합니다.
  - 저장 위치는 `save/graph/.../Trend/`입니다.

### PDF 리포트 생성
- `Slack_bot/pdf_m/create_pdf.py`
  - ReportLab으로 PDF를 생성합니다.
  - 데이터 요약, 오류 데이터 테이블, 검증 결과, 그래프를 포함합니다.
  - 저장 위치는 `save/report_pdf/...`입니다.

### 로깅
- `Slack_bot/log_m/log.py`
  - Slack 전송 및 incident 로그를 파일로 기록합니다.
  - `slack_log.txt`, `incident_log.txt`로 분리 저장합니다.
- `Slack_bot/utils/logging.py`
  - 스케줄러 및 서비스 실행 로그를 기록합니다.
  - 기본 로그 경로는 `/home/Ubicomp/bot/total_log`, 실패 시 프로젝트 내 `total_log`로 대체합니다.

### 데이터 모델
- `Slack_bot/models.py`
  - incident 데이터를 담는 `lists` 데이터클래스 정의입니다.
  - incident id, 서비스명, 상태, 발생/복구 시각 등을 보관합니다.

### 기타
- `install.txt`
  - 프로젝트에서 사용하는 pip 패키지 목록입니다.
  - `pip install -r install.txt`로 설치합니다.
- `Slack_bot/__init__.py`, `Slack_bot/utils/__init__.py`
  - 패키지 인식용 파일입니다.

## 설정 포인트 요약
- 데이터 API URL: `Slack_bot/data_m/fetch_data.py`의 `BASE_URL`
- WebSocket 주소: `incident_bot.py`의 `WEBSOCKET_URI`
- 스케줄 시간: `start.py`에서 설정

## 동작 흐름 요약
1) 스케줄러 또는 수동 실행으로 리포트 생성 시작  
2) API에서 데이터 수집 → DataFrame 생성 → 오류 처리 → 보간  
3) 센서 검증 및 통계 계산  
4) 그래프 및 PDF 생성  
5) Slack으로 결과 및 파일 전송  

Incident 리스너는 별도 프로세스로 실행되어 WebSocket 메시지를 실시간으로 Slack에 전달합니다.
