#!/usr/bin/env bash
# 把公開版三份 JSON 同步到 GitHub：開新分支 → commit → PR → 檢查 → squash 合併。
# 用法：bash tools/sync_github.sh <公開版資料夾> <M/D>
# 只印出最後結果一行：MERGED <PR網址>｜NOCHANGE｜FAIL <原因> [PR網址]
set -u
SRC=$(cd "$1" && pwd); MD=$2
TOOLS=$(cd "$(dirname "$0")" && pwd)
REPO=rayanhuang/finance-brief
cd "${FB_REPO:-$TOOLS/..}" || { echo "FAIL 找不到 repo"; exit 1; }
for f in brief snapshot history; do python3 -c "import json,sys;json.load(open(sys.argv[1]))" "$SRC/$f.json" || { echo "FAIL $f.json 不是合法 JSON"; exit 1; }; done
python3 "$TOOLS/make_public.py" --check "$SRC" >/dev/null || { echo "FAIL 公開版仍含私人內容（或找不到私人設定）"; exit 1; }
# 執行環境有指定開發分支時用 FB_BRANCH，否則每天開新分支
BR="${FB_BRANCH:-daily-data-$(TZ=Asia/Taipei date +%Y%m%d-%H%M)}"
git fetch -q origin main && git checkout -q -B "$BR" origin/main || { echo "FAIL git fetch/checkout"; exit 1; }
# 固定的開發分支前一天已被 squash 合併：把舊分支併進來（保留 main 的內容），讓這次推送是快轉，不需要強制覆寫
if git fetch -q origin "$BR" 2>/dev/null; then
  git -c user.name="${GIT_AUTHOR_NAME:-Claude}" -c user.email="${GIT_AUTHOR_EMAIL:-noreply@anthropic.com}" merge -q -s ours --no-edit FETCH_HEAD || { echo "FAIL 無法併入既有分支 $BR"; exit 1; }
fi
cp "$SRC"/brief.json "$SRC"/snapshot.json "$SRC"/history.json data/
git add data/
if git diff --cached --quiet; then echo "NOCHANGE"; exit 0; fi
git -c user.name="${GIT_AUTHOR_NAME:-Claude}" -c user.email="${GIT_AUTHOR_EMAIL:-noreply@anthropic.com}" commit -q -m "更新財經早報資料（$MD）" || { echo "FAIL commit"; exit 1; }
SHA=$(git rev-parse HEAD)
ok=""
for i in 1 2 3 4; do
  git push -q -u origin "$BR" 2>/tmp/push.err && { ok=1; break; }
  grep -q "403" /tmp/push.err && { echo "FAIL push 403：$(tail -1 /tmp/push.err)"; exit 1; }
  sleep $((i*4))
done
[ -n "$ok" ] || { echo "FAIL push：$(tail -1 /tmp/push.err)"; exit 1; }
PR=$(gh api -X POST repos/$REPO/pulls -f title="更新財經早報資料（$MD）" -f head="$BR" -f base=main \
  -f body="每日自動更新 data/ 三份公開資料；盤中、估算與約值已標註在 brief 的資料缺口與 history 的 note。" --jq '.number' 2>&1) || { echo "FAIL 建立 PR：$PR"; exit 1; }
URL="https://github.com/$REPO/pull/$PR"
# 先等 GitHub Actions「自動合併每日早報資料 PR」合併（最多約 2 分鐘）
for i in $(seq 1 12); do
  sleep 10
  m=$(gh api repos/$REPO/pulls/$PR --jq '.merged' 2>/dev/null)
  [ "$m" = "true" ] && { echo "MERGED $URL"; exit 0; }
done
# 沒有被自動合併時，才自行檢查後合併
state=""; head=""
for i in 1 2 3 4; do
  sleep 10
  read -r head state files < <(gh api repos/$REPO/pulls/$PR --jq '.head.sha+" "+.mergeable_state+" "+(.changed_files|tostring)')
  [ "$state" = "clean" ] && break
done
[ "$head" = "$SHA" ] || { echo "FAIL PR head 不符 $URL"; exit 1; }
[ "$state" = "clean" ] || { echo "FAIL mergeable_state=$state $URL"; exit 1; }
bad=$(gh api repos/$REPO/pulls/$PR/files --jq '[.[].filename|select(startswith("data/")|not)]|length')
[ "$bad" = "0" ] || { echo "FAIL PR 動到 data/ 以外的檔案 $URL"; exit 1; }
fails=$(gh api repos/$REPO/commits/$SHA/check-runs --jq '[.check_runs[]|select(.conclusion=="failure" or .conclusion=="cancelled" or .conclusion=="timed_out")]|length')
[ "$fails" = "0" ] || { echo "FAIL 檢查未通過 $URL"; exit 1; }
msg=$(gh api -X PUT repos/$REPO/pulls/$PR/merge -f merge_method=squash -f sha="$SHA" --jq '.merged' 2>&1)
if [ "$msg" = "true" ]; then echo "MERGED $URL"
elif [ "$(gh api repos/$REPO/pulls/$PR --jq '.merged' 2>/dev/null)" = "true" ]; then echo "MERGED $URL"
else echo "FAIL 合併：$msg $URL"; fi
