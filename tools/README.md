# 每日排程用的小工具

- `analyze.py history.json [--cost N]`：計算均線、漲跌幅、外資連買賣、相關係數等，印出精簡摘要。
- `make_public.py <完整版資料夾> <公開版資料夾>`：移除私人欄位並檢查洩漏，有問題以代碼 1 結束。
- `build_email.py <公開版資料夾> <輸出.html>`：產生手機版 Gmail 早報 HTML，印出主旨、純文字摘要與大小。
- `sync_github.sh <公開版資料夾> <M/D>`：開分支、commit、PR、檢查後合併，最後印出一行結果。
