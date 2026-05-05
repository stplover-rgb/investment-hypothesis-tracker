# Obsidian Vault 자동 백업 셋업

매일 자정 30분에 Obsidian vault 전체를 tar.gz로 압축 + 30일 보관.

## 1. Termux에서 폰 저장소 접근 권한

처음 한 번만:

```bash
termux-setup-storage
```

권한 요청 다이얼로그 나오면 **허용**. 이후 `~/storage/shared/` 로 폰 내부 저장소 접근 가능.

## 2. Obsidian Vault 경로 찾기

폰의 Obsidian 앱 → 좌측 메뉴 → **Manage vaults** → 사용 중인 vault 옆 점 세 개 → 경로 확인.

흔한 경로 예:
- `/storage/emulated/0/Documents/MyVault`
- `/storage/emulated/0/Obsidian/MyVault`
- `/storage/emulated/0/Download/Vault`

Termux에서 동일한 곳 확인:

```bash
ls ~/storage/shared/Documents/      # 또는 다른 폴더
```

vault 폴더 보이면 OK. 절대 경로는 `~/storage/shared/Documents/MyVault` 같은 형식.

## 3. .env에 경로 추가

```bash
echo 'OBSIDIAN_VAULT_PATH=~/storage/shared/Documents/MyVault' >> ~/projects/investment-hypothesis-tracker/.env
```

(본인 vault 이름으로 교체)

## 4. 수동 1회 실행 (검증)

```bash
cd ~/projects/investment-hypothesis-tracker
python -m jobs.obsidian_backup
```

성공하면:
- `백업 중: ... → 2026-05-05.tar.gz`
- `obsidian_backup: 12.3MB → 2026-05-05.tar.gz`
- 폰 알림: "📓 Obsidian 백업 12.3MB 완료"

확인:
```bash
ls -lh data/backups/obsidian/
```

## 5. cron 자동 등록

이미 `pixel/crontab.example` 에 다음 줄이 들어있음:
```
30 0 * * * cd $PROJ && python -m jobs.obsidian_backup >> logs/cron.log 2>&1
```

GitOps가 다음 sync 사이클에 자동 등록 (또는 수동):

```bash
crontab pixel/crontab.example
```

매일 자정 30분에 자동 백업 + 31일 넘는 거 자동 삭제.

## 6. 백업 복원 (만일의 경우)

```bash
cd ~/storage/shared/Documents/   # 복원 대상 폴더
tar -xzf ~/projects/investment-hypothesis-tracker/data/backups/obsidian/2026-05-05.tar.gz
```

`MyVault` 폴더가 풀려나옴.

## 트러블슈팅

| 증상 | 원인/해결 |
|---|---|
| `vault 경로 없음` | OBSIDIAN_VAULT_PATH 가 실제 폴더가 아님 — `ls` 로 확인 |
| `Permission denied` | `termux-setup-storage` 안 함 |
| `OBSIDIAN_VAULT_PATH 미설정` | .env 에 줄 안 추가됨 |
| 백업 파일 너무 큼 | vault 안에 .git 같은 큰 폴더가 있을 수 있음. 정리 권장 |

## 더 강력한 백업 (선택)

GitHub 프라이빗 레포에 자동 push로 영구 보관:

1. GitHub에서 `obsidian-backup` 같은 프라이빗 레포 생성
2. Termux에서 vault 폴더에 git init + remote 추가
3. 별도 스크립트 또는 이 job에 git push 추가

(필요하면 채팅에서 부탁하시면 코드 만들어드림)
