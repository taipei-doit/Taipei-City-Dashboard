#!/usr/bin/env bash
set -euo pipefail

# === 設定 ===
REPO_DIR="/opt/datacenter/Taipei-City-Dashboard/Taipei-City-Dashboard-DE/docker/prod"   # 修改成你的實際專案路徑
BRANCH="pre-develop"
LOG="/var/log/gitsync.log"
LOCK="/var/lock/gitsync.lock"

# systemd 的 PATH 很精簡，補上常見路徑
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

# 若需要指定 SSH 金鑰（可拿掉）
# export GIT_SSH_COMMAND="/usr/bin/ssh -o StrictHostKeyChecking=no"

# 鎖定避免重複執行
exec 200>"$LOCK"
flock -n 200 || { echo "$(date '+%F %T') [INFO] another run in progress" >> "$LOG"; exit 0; }

echo "$(date '+%F %T') [INFO] start gitsync" >> "$LOG"

cd "$REPO_DIR"

# 確認目前在正確分支（避免 detached HEAD）
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" != "$BRANCH" ]]; then
  git checkout "$BRANCH" >> "$LOG" 2>&1 || true
fi

# 取遠端狀態
git fetch origin "$BRANCH" >> "$LOG" 2>&1 || { echo "$(date '+%F %T') [ERROR] git fetch failed" >> "$LOG"; exit 1; }

LOCAL="$(git rev-parse HEAD)"
REMOTE="$(git rev-parse "origin/$BRANCH")"

if [[ "$LOCAL" != "$REMOTE" ]]; then
  echo "$(date '+%F %T') [INFO] changes detected: $LOCAL -> $REMOTE" >> "$LOG"
  # 你也可以用 pull --rebase；若怕衝突，用硬重置到遠端：
  git reset --hard "origin/$BRANCH" >> "$LOG" 2>&1

  # 如果有 Docker：先拉新 image，再起服務
  if command -v /usr/bin/docker >/dev/null 2>&1; then
    # 使用 docker compose（新語法）；若你用舊版 docker-compose，改成 /usr/bin/docker-compose
    /usr/bin/docker compose -f docker-compose.yaml pull >> "$LOG" 2>&1 || true
    /usr/bin/docker compose -f docker-compose.yaml up -d --remove-orphans >> "$LOG" 2>&1 || true
    # 或者只想 restart：
    # /usr/bin/docker compose restart >> "$LOG" 2>&1 || true
  fi

  echo "$(date '+%F %T') [INFO] sync & (re)deploy done" >> "$LOG"
else
  echo "$(date '+%F %T') [INFO] no changes" >> "$LOG"
fi

echo "$(date '+%F %T') [INFO] end gitsync" >> "$LOG"