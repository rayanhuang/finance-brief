#!/usr/bin/env python3
"""每日數據分析：讀 history.json，印出精簡的指標摘要（給排程寫 analysis／advice／yageo 用）。

用法：python3 tools/analyze.py history.json [--cost 870]
--cost 只在需要計算與持股成本距離時傳入；成本不寫在 repo 裡。
"""
import argparse, json, statistics

SERIES = [('taiex', '加權'), ('nasdaq', '那指'), ('sox', '費半'), ('btc', 'BTC'), ('yageo', '國巨'), ('e981a', '00981A')]


def pts(rows, k):
    return [(r['date'], r[k]) for r in rows if isinstance(r.get(k), (int, float))]


def pct(a, b):
    return (a / b - 1) * 100


def fmt(v, dp=2):
    return '資料不足' if v is None else f'{v:+.{dp}f}%'


def ma(vals, n):
    return sum(vals[-n:]) / n if len(vals) >= n else None


def corr(h, a, b, n=20):
    pa, pb = dict(pts(h, a)), dict(pts(h, b))
    ds = [d for d in sorted(pa) if d in pb]
    ra, rb = [], []
    for d0, d1 in zip(ds, ds[1:]):
        ra.append(pct(pa[d1], pa[d0])); rb.append(pct(pb[d1], pb[d0]))
    ra, rb = ra[-n:], rb[-n:]
    if len(ra) < 8:
        return None
    try:
        return statistics.correlation(ra, rb)
    except statistics.StatisticsError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('history')
    ap.add_argument('--cost', type=float)
    a = ap.parse_args()
    h = sorted(json.load(open(a.history)), key=lambda r: r['date'])
    out = []
    for k, name in SERIES:
        p = pts(h, k)
        if not p:
            continue
        v = [x for _, x in p]
        last = v[-1]
        line = [f'{name} {p[-1][0][5:]} 收 {last:,.2f}']
        line.append('5日 ' + (fmt(pct(last, v[-6])) if len(v) >= 6 else '資料不足'))
        line.append('20日 ' + (fmt(pct(last, v[-21])) if len(v) >= 21 else '資料不足'))
        mas = {}
        for n in (5, 10, 20):
            m = ma(v, n); mas[n] = m
            line.append(f'MA{n} ' + ('資料不足' if m is None else f'{m:,.2f}（乖離 {pct(last, m):+.2f}%）'))
        hi, lo = max(v), min(v)
        line.append(f'期間高 {hi:,.2f}（{pct(last, hi):+.1f}%）低 {lo:,.2f}（{pct(last, lo):+.1f}%）')
        if None not in mas.values():
            order = '多頭排列' if mas[5] > mas[10] > mas[20] else '空頭排列' if mas[5] < mas[10] < mas[20] else '糾結'
            line.append(order)
        if k == 'yageo':
            recent = v[-20:]
            line.append(f'近 20 日高 {max(recent):,.1f}／低 {min(recent):,.1f}')
            if a.cost:
                line.append(f'距成本 {a.cost:,.0f} {pct(last, a.cost):+.1f}%，回本需 {pct(a.cost, last):+.1f}%')
        out.append('；'.join(line))
    f = [x for _, x in pts(h, 'foreign')]
    if f:
        sign = f[-1] >= 0
        streak = 0
        for x in reversed(f):
            if (x >= 0) == sign:
                streak += 1
            else:
                break
        out.append(f"外資 連 {streak} 日{'買' if sign else '賣'}超；近 5 日累計 {sum(f[-5:]):+,.1f} 億；近 20 日累計 {sum(f[-20:]):+,.1f} 億")
    for k, name, unit in (('us10y', '10Y', 'bp'), ('twd', '新台幣', '分')):
        p = [x for _, x in pts(h, k)]
        if len(p) >= 6:
            d = (p[-1] - p[-6]) * 100
            out.append(f'{name} 最新 {p[-1]} 近 5 日變化 {d:+.1f} {unit}' + ('（正值＝貶值）' if k == 'twd' else ''))
    for b, name in (('sox', '費半'), ('nasdaq', '那指')):
        c = corr(h, 'taiex', b)
        out.append(f'加權與{name}近 20 日日報酬相關係數 ' + ('資料不足' if c is None else f'{c:.2f}'))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
