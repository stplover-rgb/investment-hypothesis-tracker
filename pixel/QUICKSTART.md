# 초보자용 빠른 시작 가이드

이 문서는 픽셀7에서 처음 시작하는 분을 위한 **순서대로 따라하는 9단계** 입니다.
각 단계는 "복사 → 붙여넣기 → 엔터" 수준으로 단순합니다.

---

## ⏱ 예상 소요 시간

| 단계 | 시간 |
|---|---|
| 1~5 (설치 + 검증) | 약 10분 |
| 6 (OpenDart 키 발급) | 약 5분 |
| 7~9 (실행 + 자동화) | 약 5분 |
| **합계** | **약 20분** |

---

## 1단계 — Termux 열기

폰의 앱 서랍에서 **Termux** 아이콘을 탭해서 엽니다.

검은 화면에 `$` 표시가 뜨면 OK.

## 2단계 — 한 줄 부트스트랩 실행

Termux에 다음 한 줄을 그대로 복사해 붙여넣고 엔터:

```bash
curl -fsSL https://raw.githubusercontent.com/stplover-rgb/investment-hypothesis-tracker/claude/claude-pixel-automation-KFk4C/scripts/bootstrap.sh | bash
```

이 스크립트가 자동으로:
- 필요한 패키지 설치 (Python, git, cron 등)
- 저장소 클론 (`~/projects/investment-hypothesis-tracker`)
- Python 의존성 설치
- Smoke test 실행
- `.env` 템플릿 생성

설치 도중 `Y/N` 물음이 나오면 **y** + 엔터.

## 3단계 — 알림 권한 확인

Smoke test 4번째 단계에서 폰 알림이 떴는지 확인.

알림이 **안 떴다면** Termux:API 권한 문제. 다음을 실행:

```bash
termux-notification --title "테스트" --content "안녕"
```

여전히 안 뜨면 폰 설정 → 앱 → **Termux:API** → 알림 허용 확인.

## 4단계 — 프로젝트 폴더로 이동

```bash
cd ~/projects/investment-hypothesis-tracker
```

이후 모든 명령은 이 폴더에서 실행합니다.

## 5단계 — 가설 목록 확인

```bash
cat hypotheses.yaml
```

기본으로 삼성전자, SK하이닉스 2개 가설이 들어있습니다.
나중에 본인 가설로 수정할 수 있습니다 (8단계 이후).

## 6단계 — OpenDart API 키 발급

이건 본인이 직접 해야 합니다. (5분 소요)

1. 폰 브라우저에서 https://opendart.fss.or.kr 접속
2. 우측 상단 **회원가입** → 이메일 인증
3. 로그인 후 **인증키 신청/관리** → **인증키 신청**
4. 신청 사유에 "개인 투자 분석" 정도 입력
5. 발급된 **40자리 키**를 복사

이제 키를 `.env` 파일에 넣습니다:

```bash
nano .env
```

화면에 `OPENDART_API_KEY=your_opendart_key_here` 가 보이면, `your_opendart_key_here` 부분을 복사한 키로 교체.

저장: `Ctrl+O` → 엔터 → `Ctrl+X`

(Termux에서 Ctrl은 키보드 상단의 `CTRL` 버튼)

## 7단계 — 실제 1회 실행

```bash
python -m jobs.daily_disclosure_check
```

성공하면:
- 새 공시가 있으면 화면에 출력 + 알림
- 새 공시가 없으면 조용히 종료 (정상)

`logs/` 폴더에 결과가 쌓입니다:

```bash
ls logs/
cat logs/$(date +%F).log
```

## 8단계 — cron으로 자동 실행 등록

cron 데몬 시작 (한 번만):

```bash
crond
```

부팅마다 자동으로 시작되게 하려면:

```bash
echo 'pgrep -x crond > /dev/null || crond' >> ~/.bashrc
```

스케줄 등록:

```bash
crontab pixel/crontab.example
```

확인:

```bash
crontab -l
```

평일 오전 8시에 자동 실행됩니다.

## 9단계 — 배터리 최적화 해제 (중요!)

이걸 안 하면 안드로이드가 새벽에 Termux를 죽여서 cron이 안 돕니다.

1. Termux 앱의 알림 영역에서 **Acquire Wakelock** 탭
2. 폰 설정 → 앱 → **Termux** → 배터리 → **제한 없음**
3. 같은 방법으로 **Termux:API** 도 제한 없음으로

(선택) F-Droid에서 **Termux:Boot** 추가 설치 → 부팅 시 cron 자동 시작.

---

## ✅ 셋업 완료 체크리스트

- [ ] `python -m jobs.smoke_test` 통과
- [ ] `.env`에 OpenDart 키 입력됨
- [ ] `python -m jobs.daily_disclosure_check` 1회 성공
- [ ] `crontab -l` 에 스케줄 보임
- [ ] Termux 배터리 최적화 해제

전부 체크되면 **L2 자율 에이전트가 작동 중** 입니다. 매일 아침 자동으로 돌아요.

---

## 자주 묻는 문제

**Q: `pm list packages` 가 에러 났는데?**
A: 정상입니다. Termux는 시스템 패키지 매니저를 못 부르도록 막혀 있습니다. 이 프로젝트와는 무관합니다.

**Q: `cmd: not found` 가 떠요**
A: `cd ~/projects/investment-hypothesis-tracker` 로 이동 후 다시 시도.

**Q: cron이 안 돌아요**
A: `pgrep -x crond` 로 데몬 확인. 출력 없으면 `crond` 다시 실행.

**Q: 가설 추가하고 싶어요**
A: `nano hypotheses.yaml` → 항목 추가 → 저장. 다음 cron부터 반영됨.
   corp_code(8자리)는 OpenDart 사이트에서 회사명 검색하면 나옵니다.

**Q: 다음 단계 (L3)는?**
A: MacroDroid에서 트리거 만들어 Termux 호출하기. 이미 MacroDroid 깔려있으면 절반 끝.
