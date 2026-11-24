"""讀取私人設定（持股、私人欄位清單）。設定檔放在私人存放庫，不進這個公開存放庫。

找設定檔的順序：
1. 環境變數 FB_PRIVATE
2. 與本 repo 同層的 finance-brief-private/private.json
3. 與 FB_REPO 同層的 finance-brief-private/private.json（tools 被取到別處執行時）
4. /home/user、/home/claude、家目錄底下的 finance-brief-private/private.json（排程環境）
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _candidates():
    if os.environ.get('FB_PRIVATE'):
        yield os.environ['FB_PRIVATE']
    yield os.path.join(os.path.dirname(ROOT), 'finance-brief-private', 'private.json')
    if os.environ.get('FB_REPO'):
        yield os.path.join(os.path.dirname(os.path.abspath(os.environ['FB_REPO'])), 'finance-brief-private', 'private.json')
    for base in ('/home/user', '/home/claude', os.path.expanduser('~')):
        yield os.path.join(base, 'finance-brief-private', 'private.json')


PATH = next((p for p in _candidates() if os.path.exists(p)), os.environ.get('FB_PRIVATE') or
            os.path.join(os.path.dirname(ROOT), 'finance-brief-private', 'private.json'))


def load(required=False):
    if os.path.exists(PATH):
        with open(PATH) as f:
            return json.load(f)
    if required:
        print(f'找不到私人設定 private.json（請把 rayanhuang/finance-brief-private 複製到 /home/user 或用 FB_PRIVATE 指定路徑）')
        sys.exit(1)
    return {}
