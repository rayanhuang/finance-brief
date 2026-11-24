"""讀取私人設定（持股、私人欄位清單）。設定檔放在私人存放庫，不進這個公開存放庫。

路徑：環境變數 FB_PRIVATE；沒設定時用與本 repo 同層的 finance-brief-private/private.json。
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.environ.get('FB_PRIVATE') or os.path.join(os.path.dirname(ROOT), 'finance-brief-private', 'private.json')


def load(required=False):
    if os.path.exists(PATH):
        with open(PATH) as f:
            return json.load(f)
    if required:
        print(f'找不到私人設定 {PATH}（用環境變數 FB_PRIVATE 指定路徑）')
        sys.exit(1)
    return {}
