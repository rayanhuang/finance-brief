#!/usr/bin/env python3
"""從完整版三份 JSON 產生公開版（移除個人持股相關內容），並檢查有沒有漏出去。

用法：
  python3 tools/make_public.py <完整版資料夾> <公開版資料夾>
  python3 tools/make_public.py --check <公開版資料夾>   只檢查，不產生
要移除的段落、代號、欄位與關鍵字都寫在私人設定（見 private.py）；找不到設定就拒絕執行。
檢查失敗時印出問題列並以代碼 1 結束，請改寫完整版該列（或把 tone 設成 private）後重跑。
"""
import json, os, re, sys

import private

CFG = private.load(required=True)
PRIVATE_SECTIONS = set(CFG['private_sections'])
PRIVATE_IDS = set(CFG['private_ids'])
PRIVATE_FIELDS = set(CFG['private_fields'])
LEAK = re.compile(CFG['leak'])


def check(d):
    load = lambda n: json.load(open(os.path.join(d, n + '.json')))
    h, b, s = load('history'), load('brief'), load('snapshot')
    bad = [f"history {r.get('date')}" for r in h if PRIVATE_FIELDS & r.keys()]
    bad += [f"brief {r.get('key')}" for r in b if r['section'] in PRIVATE_SECTIONS or r.get('tone') == 'private']
    bad += [f"snapshot {r.get('id')}" for r in s if r['id'] in PRIVATE_IDS]
    if bad:
        print('公開版仍含私人內容：\n' + '\n'.join(bad))
        sys.exit(1)
    print('公開版檢查通過')


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    load = lambda n: json.load(open(os.path.join(src, n + '.json')))
    b = [r for r in load('brief') if r['section'] not in PRIVATE_SECTIONS and r.get('tone') != 'private']
    s = [r for r in load('snapshot') if r['id'] not in PRIVATE_IDS]
    h = [{k: v for k, v in r.items() if k not in PRIVATE_FIELDS} for r in load('history')]
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
    print(f'公開版 OK：brief {len(b)} 列、snapshot {len(s)} 列、history {len(h)} 列')


if __name__ == '__main__':
    if sys.argv[1] == '--check':
        check(sys.argv[2])
    else:
        main(*sys.argv[1:3])
