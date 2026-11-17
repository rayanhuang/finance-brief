#!/usr/bin/env python3
"""用公開版三份 JSON 產生手機版 Gmail 早報 HTML（全 inline style、淺底深字、深色模式可讀）。

用法：python3 tools/build_email.py <公開版資料夾> <輸出.html>
brief 的 meta 列 a 為 holiday 時自動改成假日版順序。印出主旨、純文字摘要與 HTML 大小。
"""
import html, json, os, sys

UP, UPBG, DN, DNBG, NEU, NEUBG = '#d93025', '#fde8e6', '#0f8a4a', '#e3f5ea', '#5f6b7a', '#eef1f5'
NAVY, BLUE, INK = '#0f1f3d', '#2f5fb3', '#1f2a37'
DASH = 'https://claude.ai/artifact/MWk3tPrgCfug1Bx8U4a8Xf'
SITE = 'https://rayanhuang.github.io/finance-brief/'
e = lambda s: html.escape(str(s or ''))


def card(title, body, extra=''):
    t = f'<div style="font-size:17px;font-weight:700;color:{NAVY};margin:0 0 10px">{title}</div>' if title else ''
    return (f'<tr><td style="padding:0 12px 12px"><div style="background:#fff;border-radius:16px;padding:16px;'
            f'box-shadow:0 1px 3px rgba(15,31,61,.12);{extra}">{t}{body}</div></td></tr>')


def box(body, bg, color=INK, border=''):
    b = f'border-left:4px solid {border};' if border else ''
    return f'<div style="background:{bg};{b}border-radius:10px;padding:10px 12px;margin:0 0 8px;color:{color};font-size:14px;line-height:1.6">{body}</div>'


def pill(t, bg, c, border=''):
    bd = f'border:1px solid {border};' if border else ''
    return f'<span style="display:inline-block;background:{bg};color:{c};{bd}border-radius:12px;padding:1px 9px;font-size:12px;font-weight:700;margin-right:4px">{t}</span>'


def small(t, c=NEU):
    return f'<div style="font-size:12px;color:{c};margin-top:4px;line-height:1.5">{t}</div>'


def chg_txt(r):
    c = r.get('chg')
    if c is None:
        return None, NEU, NEUBG
    if r['id'] == 'twd':
        return f"{'升' if c < 0 else '貶'} {abs(c) * 100:.1f} 分", (UP if c < 0 else DN), (UPBG if c < 0 else DNBG)
    if r.get('unit') == '%' and r.get('chgKind') == 'abs':
        t = f"{'▲' if c > 0 else '▼' if c < 0 else ''}{abs(c) * 100:.0f} bp"
    elif r.get('chgKind') == 'pct':
        t = f"{'▲' if c > 0 else '▼' if c < 0 else ''}{abs(c):.2f}%"
    else:
        t = f"{'▲' if c > 0 else '▼' if c < 0 else ''}{abs(c):,g}"
    if c == 0:
        return t, NEU, NEUBG
    return t, (UP if c > 0 else DN), (UPBG if c > 0 else DNBG)


def val(r):
    v = r.get('value')
    if v is None:
        return '—'
    dp = int(r.get('dp') if r.get('dp') is not None else 2)
    s = f'{v:,.{dp}f}'
    return s + '%' if r.get('unit') == '%' else s


def main(src, out):
    B = json.load(open(os.path.join(src, 'brief.json')))
    S = json.load(open(os.path.join(src, 'snapshot.json')))
    sec = lambda s: sorted([r for r in B if r['section'] == s], key=lambda r: r['ord'])
    one = lambda s: (sec(s) or [{}])[0]
    SM = {r['id']: r for r in S}
    meta = one('meta')
    hol = meta.get('a') == 'holiday'
    y, m, d = map(int, meta['tag'].split('-'))
    import datetime
    wk = '一二三四五六日'[datetime.date(y, m, d).weekday()]
    tw_d = next((r['group'] for r in S if r['group'].startswith('台股')), '')
    us_d = next((r['group'] for r in S if r['group'].startswith('美股')), '')
    strip = lambda g: g[g.find('（') + 1:g.find('）')] if '（' in g else ''
    sub = (f'台股休市｜行情為 {strip(tw_d)}' if hol else f'台股 {strip(tw_d)}｜美股 {strip(us_d)}')
    blocks = {}

    blocks['hero'] = (f'<tr><td style="padding:12px"><div style="background:#dfe9fb;border:1px solid #c3d4f3;border-radius:16px;padding:16px">'
                      + pill('📰 假日新聞版' if hol else '📊 每日財經早報', '#ffd54f', NAVY)
                      + f'<div style="font-size:26px;font-weight:800;color:{NAVY};margin-top:8px">{m} 月 {d} 日・週{wk}</div>'
                      + f'<div style="font-size:13px;color:{BLUE};font-weight:600">{e(sub)}</div>'
                      + f'<div style="background:#fff;border-left:5px solid #f5b800;border-radius:8px;padding:12px;margin-top:12px;color:{INK};font-weight:700;font-size:15px;line-height:1.6">💬 {e(one("take").get("text"))}</div>'
                      + '</div></td></tr>')
    blocks['focus'] = card(f'<span style="color:#7a5a00">🎯 {"開盤前最該盯" if hol else "今天最該盯"}</span>',
                           f'<div style="color:#3d3200;font-size:15px;line-height:1.7">{e(one("focus").get("text"))}</div>',
                           'background:#fff7d6;border:2px solid #ffd54f;')
    adv = sec('advice')
    if adv:
        a = adv[0]
        st = {'up': (UPBG, UP), 'down': (DNBG, DN)}.get(a.get('tone'), (NEUBG, NEU))
        body = (pill(e(a.get('tag')), *st) + f'<div style="font-weight:700;color:{INK};font-size:15px;margin:8px 0;line-height:1.6">{e(a.get("text"))}</div>'
                + (box('<b>依據</b><br>' + e(a.get('a')), '#f3f5f8') if a.get('a') else '')
                + (box('<b>風險與失效</b><br>' + e(a.get('b')), '#f3f5f8') if a.get('b') else '') + small('參考建議，不保證獲利'))
        blocks['advice'] = card('🧭 今日操作建議', body, f'border:2px solid {BLUE};')

    # 三格重點
    kp = [SM.get('taiex'), SM.get('fini'), SM.get('sox') or SM.get('ixic')]
    cells = ''
    for r in [k for k in kp if k]:
        t, c, bg = chg_txt(r)
        if r['id'] == 'fini':
            v = r.get('value')
            c, bg = (NEU, NEUBG) if v is None else ((UP, UPBG) if v >= 0 else (DN, DNBG))
            t = '' if v is None else ('買超' if v >= 0 else '賣超')
        cells += (f'<td width="33%" style="padding:3px"><div style="background:{bg};border-radius:12px;padding:10px 4px;text-align:center">'
                  f'<div style="font-size:12px;color:{INK}">{e(r["name"])}</div><div style="font-size:18px;font-weight:800;color:{c}">{val(r)}</div>'
                  f'<div style="font-size:12px;font-weight:700;color:{c}">{e(t or "")}</div></div></td>')
    note = f'（{strip(tw_d)} 收盤・休市中）' if hol else ''
    blocks['kpi'] = f'<tr><td style="padding:0 9px 12px"><table width="100%" cellpadding="0" cellspacing="0"><tr>{cells}</tr></table></td></tr>'

    # 市場數字
    groups = [('🇹🇼 台股', '台股'), ('🇺🇸 美股・期指', '美股'), ('🌏 利率・商品', '其他'), ('🪙 加密', '加密')]
    mk = ''
    for label, pre in groups:
        rows = [r for r in S if r['group'].startswith(pre)]
        if not rows:
            continue
        mk += f'<div style="font-size:14px;font-weight:700;color:{BLUE};margin:10px 0 2px">{label}</div><table width="100%" cellpadding="0" cellspacing="0" style="font-size:13px;color:{INK}">'
        for i in range(0, len(rows), 2):
            mk += '<tr>'
            for r in rows[i:i + 2]:
                t, c, bg = chg_txt(r)
                unit = '' if r.get('unit') in ('%', None) else r['unit']
                ch = f' <span style="background:{bg};color:{c};border-radius:8px;padding:0 5px;font-size:12px">{t}</span>' if t else ''
                mk += f'<td width="50%" style="padding:4px 4px;border-bottom:1px solid #eef1f5">{e(r["name"])}<br><b>{val(r)}</b> {e(unit)}{ch}</td>'
            mk += '<td></td></tr>' if len(rows[i:i + 2]) == 1 else '</tr>'
        mk += '</table>'
    blocks['market'] = card('📈 市場數字' + note, mk)
    blocks['landed'] = card('🗳️ 剛落地的大事', f'<div style="font-size:14px;color:{INK};line-height:1.7">{e(one("landed").get("text"))}</div>')

    T = {'up': (UP, UPBG, '🔺利多'), 'down': (DN, DNBG, '🔻利空')}
    nw = ''
    for i, n in enumerate(sec('news'), 1):
        c, bg, l = T.get(n.get('tone'), (NEU, NEUBG, '◆中性'))
        nw += (f'<div style="border-left:5px solid {c};background:#fafbfc;border-radius:10px;padding:10px 12px;margin-bottom:10px">'
               f'<span style="font-size:20px;font-weight:800;color:#9aa3ae;margin-right:6px">{i:02d}</span>{pill(l, bg, c)}{pill("#" + e(n.get("tag")), "#e8effc", BLUE)}'
               f'<div style="font-size:14px;color:{INK};margin-top:6px;line-height:1.6">{e(n.get("text"))}</div>'
               + (box('📊 市場反應：' + e(n.get('a')), NEUBG, '#3c4652') if n.get('a') else '') + '</div>')
    blocks['news'] = card('📰 重大新聞', nw)

    cal = ''
    for c in sec('calendar'):
        ev, _, why = str(c.get('text', '')).partition('——')
        a = c.get('a', '')
        bg, col = (UPBG, UP) if a == '今天' else ('#fff1dc', '#c66a00') if a in ('倒數 1 天', '倒數 2 天') else ('#e8effc', BLUE)
        cal += (f'<tr><td width="76" style="vertical-align:top;padding:0 0 8px"><div style="background:#e8effc;border:1px solid #c3d4f3;border-radius:8px;text-align:center;font-size:12px;font-weight:700;color:{NAVY};padding:5px 2px">{e(c.get("tag"))}</div></td>'
                f'<td style="vertical-align:top;padding:0 0 8px 8px;font-size:14px;color:{INK}">{pill(e(a), bg, col)}<b>{e(ev)}</b>'
                + (f'<br><span style="font-size:12px;color:{NEU}">{e(why)}</span>' if why else '') + '</td></tr>')
    blocks['calendar'] = card('🗓️ 宏觀日曆', f'<table width="100%" cellpadding="0" cellspacing="0">{cal}</table>')

    ins = {r['tag']: r for r in sec('insight')}
    ib = ''
    if '資金流向' in ins:
        ib += box('<b>💸 資金流向</b><br>' + e(ins['資金流向']['text']), '#f6f8fb')
    if '板塊輪動' in ins:
        t = ins['板塊輪動']['text']
        strong, _, weak = t.partition('；')
        ib += box('<b>🔥 強勢</b><br>' + e(strong.replace('強勢＝', '')), UPBG, INK)
        if weak:
            ib += box('<b>🧊 弱勢</b><br>' + e(weak.replace('弱勢＝', '')), DNBG, INK)
    if '一句話' in ins:
        ib += f'<div style="font-size:17px;font-weight:700;color:{NAVY};text-align:center;padding:10px 6px;line-height:1.6">「{e(ins["一句話"]["text"])}」</div>'
    if '觀察指標' in ins:
        import re
        parts = [p.strip(' ；;') for p in re.split(r'\(\d\)', ins['觀察指標']['text']) if p.strip(' ；;')]
        ib += '<div style="font-weight:700;color:' + INK + ';margin:6px 0">👀 觀察指標</div>'
        for i, p in enumerate(parts, 1):
            ib += (f'<table cellpadding="0" cellspacing="0" style="margin-bottom:6px"><tr><td style="vertical-align:top"><div style="width:22px;height:22px;border-radius:11px;background:#e8effc;border:1px solid {BLUE};color:{BLUE};font-size:12px;font-weight:700;text-align:center;line-height:22px">{i}</div></td>'
                   f'<td style="padding-left:8px;font-size:14px;color:{INK};line-height:1.6">{e(p)}</td></tr></table>')
    blocks['insight'] = card('💡 洞察', ib)

    tw = ''
    for t in sec('tw'):
        bg, c, ic = (UPBG, UP, '📈') if t.get('tone') == 'up' else (DNBG, DN, '📉') if t.get('tone') == 'down' else ('#e8effc', BLUE, '🔍')
        tw += box(f'<b style="color:{c}">{ic} {e(t.get("tag"))}</b><br>' + e(t.get('text')), bg)
    blocks['tw'] = card('🇹🇼 對台股的影響', tw)

    bd = {r['tag']: r for r in sec('board')}
    bb = ''
    if '核心矛盾' in bd:
        t = bd['核心矛盾']['text']
        bull, _, bear = t.partition(' vs ')
        bull = bull.replace('「多方力量」', '').strip()
        bear = bear.replace('「空方疑慮」', '').strip()
        bb += (f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
               f'<td width="50%" style="padding-right:4px;vertical-align:top">{box("<b>🐂 多方力量</b><br>" + e(bull), UPBG)}</td>'
               f'<td width="50%" style="padding-left:4px;vertical-align:top">{box("<b>🐻 空方疑慮</b><br>" + e(bear or "—"), DNBG)}</td></tr></table>')
    if '最重要事件' in bd:
        t = bd['最重要事件']['text']
        head, _, rest = t.partition('多方推演')
        bull, _, bear = rest.partition('空方推演')
        bb += box('<b>⭐ 最重要事件</b><br>' + e(head.strip('。 ')), '#fff7d6', '#3d3200')
        if bull:
            bb += box('<b style="color:' + UP + '">多方劇本</b> ' + e(bull.strip('→；; ')), UPBG)
        if bear:
            bb += box('<b style="color:' + DN + '">空方劇本</b> ' + e(bear.strip('→；; ')), DNBG)
    if '關鍵價位' in bd:
        bb += box('<b>📍 關鍵價位</b><br>' + e(bd['關鍵價位']['text']), '#f3f5f8')
    blocks['board'] = card('⚔️ 多空對決', bb)

    L = {'觸發': ('🔴', UP, UPBG), '觀察中': ('🟠', '#c66a00', '#fff1dc'), '未觸發': ('🟢', DN, DNBG)}
    al = ''
    for a in sec('alert'):
        ic, c, bg = L.get(a.get('b'), L['觀察中'])
        al += box(f'<b>{ic} {e(a.get("tag"))}</b> {pill(e(a.get("b")), "#fff", c, c)}<br>{e(a.get("text"))}' + small('解除：' + e(a.get('a'))), bg)
    al += f'<div style="font-size:16px;font-weight:700;color:{NAVY};margin:12px 0 8px">🧭 條件觸發劇本</div>'
    for t in sec('trigger'):
        al += box(e(t.get('text')) + small('✅ 確認：' + e(t.get('a')), DN) + small('❌ 失效：' + e(t.get('b')), UP), '#fafbfc')
    blocks['alert'] = card('🚨 警戒燈號', al)

    an = ''
    for r in sec('analysis'):
        bg = {'up': UPBG, 'down': DNBG}.get(r.get('tone'), NEUBG)
        an += box(f'<b>{e(r.get("tag"))}</b>　{e(r.get("text"))}' + (small(e(r.get('a'))) if r.get('a') else ''), bg)
    if an:
        blocks['analysis'] = card('🔬 每日數據分析', an)

    blocks['button'] = (f'<tr><td style="padding:4px 12px 14px;text-align:center"><a href="{DASH}" style="display:inline-block;background:#e8effc;border:2px solid {BLUE};color:#1d4fa8;'
                        f'border-radius:24px;padding:10px 22px;font-weight:700;font-size:15px;text-decoration:none">📊 開啟完整儀表板 →</a>'
                        + small(f'儀表板需登入 Claude；本郵件內容已完整・公開版：<a href="{SITE}" style="color:{BLUE}">{SITE}</a>') + '</td></tr>')
    gp = ''.join(f'<div>• {e(g.get("text"))}</div>' for g in sec('gap')[:5])
    sr = ''.join(f'<div>• <a href="{e(s.get("url"))}" style="color:{BLUE}">{e(s.get("text"))}</a></div>' for s in sec('source')[:8] if str(s.get('url', '')).startswith('https://'))
    blocks['foot'] = card('', f'<div style="font-size:12px;color:{NEU};line-height:1.6"><b>🧩 資料缺口</b>{gp}<br><b>🔗 主要來源</b>{sr}'
                          f'<div style="text-align:center;margin-top:10px">本報為市場資訊整理與參考建議，不保證獲利</div></div>')

    order = (['hero', 'news', 'calendar', 'landed', 'focus', 'advice', 'kpi', 'market', 'insight', 'tw', 'board', 'alert', 'analysis', 'button', 'foot'] if hol else
             ['hero', 'focus', 'advice', 'kpi', 'market', 'landed', 'news', 'calendar', 'insight', 'tw', 'board', 'alert', 'analysis', 'button', 'foot'])
    body = ''.join(blocks[k] for k in order if k in blocks)
    doc = (f'<div style="background:#e9eef5;padding:8px 0;font-family:-apple-system,BlinkMacSystemFont,\'PingFang TC\',\'Noto Sans TC\',\'Microsoft JhengHei\',sans-serif">'
           f'<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto">{body}</table></div>')
    open(out, 'w').write(doc)
    subject = f"{'📰' if hol else '📊'} 財經早報 {m}/{d}（週{wk}{'・假日新聞版' if hol else ''}）"
    news = sec('news')[:3]
    plain = '\n'.join([str(one('take').get('text', ''))] + [f'・{n["text"][:60]}' for n in news] + [f'完整內容：{SITE}'])
    print(json.dumps({'subject': subject, 'body': plain, 'bytes': len(doc.encode())}, ensure_ascii=False, indent=1))
    if len(doc.encode()) > 60000:
        print('警告：超過 60KB，Gmail 可能截斷', file=sys.stderr)


if __name__ == '__main__':
    main(*sys.argv[1:3])
