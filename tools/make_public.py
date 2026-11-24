#!/usr/bin/env python3
"""從完整版三份 JSON 產生公開版（移除個人持股相關內容），並檢查有沒有漏出去。

用法：
  python3 tools/make_public.py <完整版資料夾> <公開版資料夾>
  python3 tools/make_public.py --check <公開版資料夾>   只檢查，不產生
要移除的段落、代號、欄位與關鍵字寫在私人設定（見 private.py）。
找不到私人設定時（例如排程拿不到私人存放庫），改用 public_fields.json 的允許清單：只保留公開欄位、段落與代號。
檢查失敗時印出問題列並以代碼 1 結束，請改寫完整版該列（或把 tone 設成 private）後重跑。
"""
import json, os, re, sys

import private

HERE = os.path.dirname(os.path.abspath(__file__))
ALLOW = json.load(open(os.path.join(HERE, 'public_fields.json')))
CFG = private.load()
FALLBACK = not CFG
if FALLBACK:
    print('（找不到私人設定，改用公開允許清單：只保留公開欄位、段落與代號）', file=sys.stderr)
LEAK = re.compile(CFG['leak'] if CFG else r'我的成本|持股成本|我的持股')


def is_private_row(section=None, tone=None, sid=None):
    if tone == 'private':
        return True
    if section is not None:
        return section not in ALLOW['brief'] if FALLBACK else section in CFG['private_sections']
    if sid is not None:
        return sid not in ALLOW['snapshot'] if FALLBACK else sid in CFG['private_ids']
    return False


def private_fields(keys):
    return set(keys) - set(ALLOW['history']) if FALLBACK else set(keys) & set(CFG['private_fields'])


def check(d):
    load = lambda n: json.load(open(os.path.join(d, n + '.json')))
    h, b, s = load('history'), load('brief'), load('snapshot')
    bad = [f"history {r.get('date')}" for r in h if private_fields(r.keys())]
    bad += [f"brief {r.get('key')}" for r in b if is_private_row(section=r['section'], tone=r.get('tone'))]
    bad += [f"snapshot {r.get('id')}" for r in s if is_private_row(sid=r['id'])]
    if bad:
        print('公開版仍含私人內容：\n' + '\n'.join(bad))
        sys.exit(1)
    print('公開版檢查通過')


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    load = lambda n: json.load(open(os.path.join(src, n + '.json')))
    b = [r for r in load('brief') if not is_private_row(section=r['section'], tone=r.get('tone'))]
    s = [r for r in load('snapshot') if not is_private_row(sid=r['id'])]
    h = [{k: v for k, v in r.items() if k not in private_fields(r.keys())} for r in load('history')]
    problems = []
    for r in b:
        if r['section'] == 'news':
            continue  # 一般新聞剛好報導到持股公司時可以保留
        txt = ' '.join(str(r.get(k, '')) for k in ('tag', 'text', 'a', 'b'))
        if LEAK.search(txt):
            problems.append(f"brief {r['key']}: {LEAK.search(txt).group()}")
    for r in s:
        if LEAK.search(json.dumps(r, ensure_ascii=False)):
            problems.append(f"snapshot {r['id']}")
    for r in h:
        if LEAK.search(str(r.get('note', ''))):
            problems.append(f"history {r['date']} note")
    for n, d in (('brief', b), ('snapshot', s), ('history', h)):
        json.dump(d, open(os.path.join(dst, n + '.json'), 'w'), ensure_ascii=False)
    if problems:
        print('可能洩漏私人內容：\n' + '\n'.join(problems))
        sys.exit(1)
    print(f"公開版 OK{'（允許清單模式）' if FALLBACK else ''}：brief {len(b)} 列、snapshot {len(s)} 列、history {len(h)} 列")


if __name__ == '__main__':
    if sys.argv[1] == '--check':
        check(sys.argv[2])
    else:
        main(*sys.argv[1:3])
