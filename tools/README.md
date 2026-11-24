# 每日排程用的小工具

- `prep.py [--out quotes.json]`：判斷今天是否為台股交易日（內建證交所休市表），並在網路允許時一次抓好指數、個股、匯率、商品、加密、三大法人與恐懼貪婪指數。
- `analyze.py history.json [--cost N]`：計算均線、漲跌幅、外資連買賣、相關係數等，印出精簡摘要。
- `make_public.py <完整版資料夾> <公開版資料夾>`：移除私人欄位並檢查洩漏，有問題以代碼 1 結束。
- `build_email.py <公開版資料夾> <輸出.html>`：產生手機版 Gmail 早報 HTML，印出主旨、純文字摘要與大小。
- `sync_github.sh <公開版資料夾> <M/D>`：開分支、commit、PR，等 GitHub Actions 自動合併（約 2 分鐘內沒合併才自行檢查後合併），最後印出一行結果。
  腳本不在 repo 裡執行時，用環境變數 FB_REPO 指定 repo 路徑。

## 私人設定（持股只放在私人存放庫）

持股名稱、股數、成本，以及公開版要移除的段落／代號／欄位，都寫在私人存放庫的 `private.json`，這個公開 repo 裡不寫任何持股資訊。

- 找設定檔的順序：環境變數 `FB_PRIVATE` → 與本 repo 同層 → 與 `FB_REPO` 同層 → `/home/user`、`/home/claude`、家目錄底下的 `finance-brief-private/private.json`。
- `make_public.py`、`sync_github.sh` 找不到私人設定時（例如排程環境沒有附上私人存放庫），改用 `public_fields.json` 的允許清單：只保留公開欄位、段落與代號，早報照常產生。
- `prep.py`、`analyze.py` 沒有私人設定時照常執行，只是不含持股。
- GitHub Actions 的自動合併改用「允許清單」：公開資料出現新的欄位、段落或代號時不會自動合併，由 `sync_github.sh` 用私人設定檢查後再合併。新增公開欄位時，記得一併加到 `tools/public_fields.json`（make_public.py 備案與自動合併共用）。
