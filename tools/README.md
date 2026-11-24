# 每日排程用的小工具

- `prep.py [--out quotes.json]`：判斷今天是否為台股交易日（內建證交所休市表），並在網路允許時一次抓好指數、個股、匯率、商品、加密、三大法人與恐懼貪婪指數。
- `analyze.py history.json [--cost N]`：計算均線、漲跌幅、外資連買賣、相關係數等，印出精簡摘要。
- `make_public.py <完整版資料夾> <公開版資料夾>`：移除私人欄位並檢查洩漏，有問題以代碼 1 結束。
- `build_email.py <公開版資料夾> <輸出.html>`：產生手機版 Gmail 早報 HTML，印出主旨、純文字摘要與大小。
- `sync_github.sh <公開版資料夾> <M/D>`：開分支、commit、PR，等 GitHub Actions 自動合併（約 2 分鐘內沒合併才自行檢查後合併），最後印出一行結果。
  腳本不在 repo 裡執行時，用環境變數 FB_REPO 指定 repo 路徑。
