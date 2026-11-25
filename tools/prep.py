#!/usr/bin/env python3
"""每日排程第一步：判斷今天是交易日或假日，並（網路允許時）一次抓好主要行情。

用法：python3 tools/prep.py [--out quotes.json]
- 交易日判斷用內建的證交所休市表，不需要連網；表外的日期會印「休市表未涵蓋」。
- 行情：Yahoo（指數、個股、匯率、商品、加密）、證交所（三大法人）、alternative.me（加密恐懼貪婪）。
  第一個請求連不上就停止，不浪費時間；印出的每一列是一個來源，數字仍需與新聞核對關鍵值。
"""
import argparse, datetime as dt, json, sys, time, urllib.parse, urllib.request

import private

# 證交所公告的休市日（不含週末）。來源：twse.com.tw 市場開休市日期（115、116 年）。
CLOSED = {
    '2026-12-25',
    '2027-01-01', '2027-02-02', '2027-02-03', '2027-02-04', '2027-02-05', '2027-02-08', '2027-02-09',
    '2027-02-10', '2027-03-01', '2027-04-05', '2027-04-06', '2027-04-30', '2027-06-09', '2027-09-15',
    '2027-09-28', '2027-10-11', '2027-10-25', '2027-12-24', '2027-12-31',
}
COVERED_UNTIL = dt.date(2027, 12, 31)

YAHOO = [
    ('dji', '^DJI'), ('spx', '^GSPC'), ('ixic', '^IXIC'), ('sox', '^SOX'), ('vix', '^VIX'),
    ('tsm', 'TSM'), ('nvda', 'NVDA'), ('amd', 'AMD'), ('aapl', 'AAPL'), ('msft', 'MSFT'),
    ('taiex', '^TWII'), ('tw2330', '2330.TW'), ('tw2454', '2454.TW'), ('tw2308', '2308.TW'), ('tw2317', '2317.TW'), ('tw3711', '3711.TW'),
    ('btc', 'BTC-USD'), ('eth', 'ETH-USD'),
    ('us10y', '^TNX'), ('us30y', '^TYX'), ('twd', 'TWD=X'), ('wti', 'CL=F'), ('brent', 'BZ=F'),
    ('gold', 'GC=F'), ('dxy', 'DX-Y.NYB'),
] + [tuple(x) for x in private.load().get('yahoo', [])]  # 持股行情只寫在私人設定
UA = {'User-Agent': 'Mozilla/5.0'}


def is_open(d):
    return d.weekday() < 5 and d.isoformat() not in CLOSED


def get(url, timeout=8):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='quotes.json')
    a = ap.parse_args()
    tpe = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    today = tpe.date()
    wk = '一二三四五六日'[today.weekday()]
    prev = today - dt.timedelta(days=1)
    while not is_open(prev):
        prev -= dt.timedelta(days=1)
    if today > COVERED_UNTIL:
        status = '休市表未涵蓋（週末以外請用 WebSearch 查一次）'
    else:
        status = '交易日' if is_open(today) else '假日（台股休市）'
    print(f'台北 {tpe:%Y-%m-%d %H:%M} 週{wk}｜{status}｜上一個台股交易日 {prev}')

    out = {'fetched_at': tpe.isoformat(timespec='minutes'), 'quotes': {}}
    syms = [s for _, s in YAHOO]
    results = []
    try:
        for i in range(0, len(syms), 20):  # 這個端點一次最多 20 檔
            sp = get('https://query1.finance.yahoo.com/v7/finance/spark?' + urllib.parse.urlencode(
                {'symbols': ','.join(syms[i:i + 20]), 'range': '5d', 'interval': '1d'}))
            results += sp['spark']['result']
    except Exception as e:  # 網路不通就直接結束，不再嘗試其他來源
        print(f'行情：連不上（{type(e).__name__}: {e}），改用搜尋')
        json.dump(out, open(a.out, 'w'), ensure_ascii=False)
        return
    by_sym = {r['symbol']: r['response'][0] for r in results if r.get('response')}
    lines = []
    for key, sym in YAHOO:
        r = by_sym.get(sym)
        if not r:
            continue
        m = r['meta']
        tz = dt.timezone(dt.timedelta(seconds=m.get('gmtoffset', 0)))
        pts = [(dt.datetime.fromtimestamp(t, tz).date().isoformat(), c)
               for t, c in zip(r.get('timestamp', []), r['indicators']['quote'][0]['close']) if c is not None]
        # Yahoo 有時最後一根日 K 的收盤是空值（例如 ^TWII），這時改用 meta 的最新成交價補上那一天，
        # 不然會把前一天的收盤當成今天（2026-11-25 加權指數就因此顯示舊值）
        rmp, rmt = m.get('regularMarketPrice'), m.get('regularMarketTime')
        if rmp is not None and rmt:
            rd = dt.datetime.fromtimestamp(rmt, tz).date().isoformat()
            if pts and rd > pts[-1][0]:
                pts.append((rd, rmp))
        if len(pts) < 2:
            continue
        (d0, c0), (d1, c1) = pts[-2], pts[-1]
        q = {'value': round(c1, 4), 'prev': round(c0, 4), 'prev_date': d0, 'date': d1, 'src': 'Yahoo ' + sym}
        end = m.get('currentTradingPeriod', {}).get('regular', {}).get('end', 0)
        today_mkt = dt.datetime.now(tz).date().isoformat()
        start = m.get('currentTradingPeriod', {}).get('regular', {}).get('start', 0)
        if (d1 == today_mkt and start <= time.time() < end) or m.get('instrumentType') == 'CRYPTOCURRENCY':
            q['partial'] = True  # 盤中或 24 小時市場：不是收盤價
        if key in ('us10y', 'us30y'):
            q['chg_bp'] = round((c1 - c0) * 100, 1)
        elif key == 'twd':
            q['chg'] = round(c1 - c0, 4)
        else:
            q['chg_pct'] = round((c1 / c0 - 1) * 100, 2)
        out['quotes'][key] = q
        chg = q.get('chg_pct', q.get('chg_bp', q.get('chg')))
        lines.append(f'{key} {q["value"]:,} ({chg:+}) {d1}' + ('（盤中／約值）' if q.get('partial') else ''))
    try:
        ymd = prev.strftime('%Y%m%d') if not is_open(today) or tpe.hour < 15 else today.strftime('%Y%m%d')
        f = get(f'https://www.twse.com.tw/rwd/zh/fund/BFI82U?response=json&dayDate={ymd}')
        rows = {r[0]: float(r[3].replace(',', '')) / 1e8 for r in f.get('data', [])}
        if rows:
            inst = {'fini': rows.get('外資及陸資(不含外資自營商)', 0) + rows.get('外資自營商', 0),
                    'sitc': rows.get('投信'), 'dealer': rows.get('自營商(自行買賣)', 0) + rows.get('自營商(避險)', 0),
                    'inst': rows.get('合計')}
            for k, v in inst.items():
                out['quotes'][k] = {'value': round(v, 2), 'unit': '億元', 'date': f'{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}', 'src': '證交所 BFI82U'}
            lines.append('法人(億) ' + ' '.join(f'{k} {v:+,.2f}' for k, v in inst.items()) + f' {ymd}')
    except Exception as e:
        lines.append(f'法人：抓取失敗（{type(e).__name__}）')
    # Yahoo 偶爾漏掉台股某天的收盤（例如 2026-11-24 加權與部分 ETF 是空值），
    # 改用證交所每日收盤行情（MI_INDEX）補正最近一個已收盤交易日的台股項目
    try:
        ymd = prev.strftime('%Y%m%d') if not is_open(today) or tpe.hour < 15 else today.strftime('%Y%m%d')
        d = f'{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}'
        j = get(f'https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={ymd}&type=ALLBUT0999&response=json', timeout=20)
        num = lambda s: float(str(s).replace(',', '')) if str(s).replace(',', '').replace('.', '').isdigit() else None
        sign = lambda s: -1 if '-' in str(s) else 1
        tw = {}
        for t in j.get('tables', []) if j.get('stat') == 'OK' else []:
            title = t.get('title') or ''
            for r in t.get('data', []):
                if '價格指數' in title and r[0] == '發行量加權股價指數' and num(r[1]):
                    tw['^TWII'] = (num(r[1]), sign(r[2]) * (num(r[3]) or 0))
                elif '每日收盤行情' in title and num(r[8]):
                    tw[r[0].strip()] = (num(r[8]), sign(r[9]) * (num(r[10]) or 0))
        fixed = []
        for key, sym in YAHOO:  # noqa
            code = '^TWII' if sym == '^TWII' else sym[:-3] if sym.endswith('.TW') else None
            q = out['quotes'].get(key)
            if code not in tw:
                continue
            c, chg = tw[code]
            if q and q.get('date', '') > d:  # Yahoo 已有今天盤中值：只修正它比較的前一日收盤
                if q.get('prev_date') != d and 'chg_pct' in q:
                    q.update(prev=c, prev_date=d, chg_pct=round((q['value'] / c - 1) * 100, 2))
                    fixed.append(f'{key} 前收改為 {d} 的 {c:,}（盤中 {q["chg_pct"]:+.2f}）')
                continue
            if q and q.get('date') == d and not q.get('partial') and abs(q['value'] - c) < 1e-6:
                continue
            p = c - chg
            out['quotes'][key] = {'value': c, 'prev': round(p, 4), 'date': d, 'src': '證交所 MI_INDEX', 'chg_pct': round((c / p - 1) * 100, 2)}
            fixed.append(f'{key} {c:,}（{(c / p - 1) * 100:+.2f}）')
        if fixed:
            lines.append(f'證交所收盤補正 {d}（Yahoo 缺值或不同，以證交所為準）：' + '、'.join(fixed))
    except Exception as e:
        lines.append(f'證交所收盤補正：抓取失敗（{type(e).__name__}）')
    try:
        g = get('https://api.alternative.me/fng/?limit=2')['data']
        out['quotes']['fng'] = {'value': int(g[0]['value']), 'chg': int(g[0]['value']) - int(g[1]['value']),
                                'label': g[0]['value_classification'], 'src': 'alternative.me'}
        lines.append(f'fng {g[0]["value"]} ({g[0]["value_classification"]})')
    except Exception as e:
        lines.append(f'fng：抓取失敗（{type(e).__name__}）')
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('行情（日期為各市場最後收盤日；twd 為 Yahoo 即時匯率，非 16:00 官方收盤）：')
    print('\n'.join(lines))
    print(f'已寫入 {a.out}')


if __name__ == '__main__':
    main()
