# Investment Hypothesis Tracker

투자 가설을 등록하고, 관련 종목의 공시 이벤트를 자동으로 모니터링하여
가설 검증 신호를 알리는 시스템.

픽셀7 + Termux + cron 환경에서 자율 실행되도록 설계됨 (자율성 L2).

## 구조

```
.
├── hypotheses.yaml          # 추적 중인 가설 정의
├── lib/                     # 공용 모듈
│   ├── opendart.py          # OpenDart API 클라이언트
│   ├── hypotheses.py        # 가설 로더
│   └── notify.py            # 알림 채널
├── jobs/
│   └── daily_disclosure_check.py   # 매일 실행되는 공시 체크
├── pixel/                   # Termux/cron 셋업 자료
│   ├── SETUP.md
│   └── crontab.example
└── data/
    └── state/               # 실행 상태 (gitignored)
```

## 빠른 시작 (데스크탑)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env에 OPENDART_API_KEY 입력 (https://opendart.fss.or.kr 가입 후 무료 발급)

python -m jobs.daily_disclosure_check
```

## 픽셀7 Termux 자동화

[`pixel/SETUP.md`](pixel/SETUP.md) 참조.

## 가설 추가

`hypotheses.yaml`에 항목을 추가하고 커밋:

```yaml
- id: H002
  title: 한 줄 요약
  corp_name: 회사명
  corp_code: "00126380"        # OpenDart 고유번호 (8자리)
  watch_keywords: [키워드1, 키워드2]
  status: active
```
