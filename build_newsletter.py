"""
build_newsletter.py — 수집 모듈 3개 결과를 합쳐 HTML 뉴스레터 본문 한 장 생성 (Step 3, 범위 "가")
설계: KRX update_html.py 대응 (조립만 담당. 수집은 각 모듈, 발송·자동화는 다음 단계)
실행: python build_newsletter.py  →  crypto_newsletter.html 생성  →  start로 브라우저 확인
"""
import datetime
import os

import crypto_fetch
import crypto_news
from render_bills import render_html   # 법안 섹션: 기존 함수 그대로 재사용

# ── 공통 스타일 ──────────────────────────
H2  = "font-size:18px;color:#111;border-bottom:2px solid #111;padding-bottom:8px;margin-top:32px;"
WHY = "font-size:12px;color:#888;margin:6px 0 14px;"


def _pct(v):
    """변동률 → 색·부호 붙인 span. None이면 — 표시."""
    if v is None:
        return '<span style="color:#999;">—</span>'
    color = "#2f8f5b" if v >= 0 else "#c0392b"
    sign  = "+" if v >= 0 else ""
    return f'<span style="color:{color};font-weight:600;">{sign}{v:.2f}%</span>'


def _section_prices(prices):
    rows = ""
    for c in prices:
        rows += f'''
        <tr>
          <td style="padding:8px 10px;font-weight:700;border-top:1px solid #eee;">{c['코인']}</td>
          <td style="padding:8px 10px;text-align:right;border-top:1px solid #eee;">{c['현재가']:,.0f}</td>
          <td style="padding:8px 10px;text-align:right;border-top:1px solid #eee;">{_pct(c['24h%'])}</td>
          <td style="padding:8px 10px;text-align:right;border-top:1px solid #eee;">{_pct(c['7d%'])}</td>
          <td style="padding:8px 10px;text-align:right;border-top:1px solid #eee;">{_pct(c['30d%'])}</td>
          <td style="padding:8px 10px;text-align:right;border-top:1px solid #eee;">{_pct(c['전고점대비%'])}</td>
        </tr>'''
    return f'''
    <h2 style="{H2}">① 시세 · 변동성</h2>
    <div style="{WHY}">모든 판단의 기준선 — 7일/30일 추세로 지금 위치 확인</div>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <tr style="background:#f0f1f3;color:#555;font-size:12px;">
        <th style="padding:8px 10px;text-align:left;">코인</th>
        <th style="padding:8px 10px;text-align:right;">현재가(KRW)</th>
        <th style="padding:8px 10px;text-align:right;">24h</th>
        <th style="padding:8px 10px;text-align:right;">7d</th>
        <th style="padding:8px 10px;text-align:right;">30d</th>
        <th style="padding:8px 10px;text-align:right;">전고점대비</th>
      </tr>
      {rows}
    </table>'''


def _card(title, body, why):
    return f'''
    <div style="border:1px solid #e4e6e9;border-radius:8px;padding:14px 16px;margin:10px 0;">
      <div style="font-size:13px;color:#888;">{title}</div>
      <div style="font-size:17px;font-weight:700;color:#111;margin:4px 0;">{body}</div>
      <div style="font-size:11px;color:#aaa;">{why}</div>
    </div>'''


def _section_indicators(fg, funding, stable, halving):
    funding_body = " · ".join(f"{f['심볼']} {f['펀딩비%']:+.4f}%" for f in funding)
    stable_b = stable['총시총_USD'] / 1e9
    cards = (
        _card("공포탐욕지수", f"{fg['값']} ({fg['분류']})", "극단 공포=누적 / 극단 탐욕=분산")
        + _card("펀딩비 (참고)", funding_body, "롱/숏 과열 — 장기엔 참고만")
        + _card("스테이블코인 시총", f"${stable_b:,.1f}B", "시장 대기 매수 유동성 프록시")
        + _card("다음 반감기", f"D-{halving['D-day']}  ({halving['다음반감기_추정']})", "4년 주기 사이클 앵커 [추정]")
    )
    return f'''
    <h2 style="{H2}">② 시장 심리 · 유동성 · 사이클</h2>
    {cards}'''


def _section_news(news):
    cats = {}
    for n in news:
        cats.setdefault(n['분류'], []).append(n)
    blocks = ""
    for cat, arts in cats.items():
        items = ""
        for a in arts:
            src = a.get('출처') or ''
            items += f'''
            <li style="margin:7px 0;font-size:13px;line-height:1.4;">
              <a href="{a['링크']}" style="color:#1a4ba8;text-decoration:none;">{a['제목']}</a>
              <span style="color:#aaa;font-size:11px;"> · {src} · {a['언어']}</span>
            </li>'''
        blocks += f'''
        <div style="margin-bottom:16px;">
          <div style="font-weight:700;color:#111;font-size:14px;margin-bottom:4px;">{cat}</div>
          <ul style="margin:0;padding-left:18px;">{items}</ul>
        </div>'''
    return f'''
    <h2 style="{H2}">④ 뉴스 헤드라인</h2>
    <div style="{WHY}">법률·기술·지정학 중장기 내러티브 (최근 7일)</div>
    {blocks}'''


def build_html():
    # ── 수집 (각 모듈 함수 호출만) ──
    prices  = crypto_fetch.fetch_prices()
    fg      = crypto_fetch.fetch_fear_greed()
    stable  = crypto_fetch.fetch_stablecoin_mcap()
    funding = crypto_fetch.fetch_funding_rates()
    halving = crypto_fetch.halving_countdown()
    news    = crypto_news.fetch_news()
    bills_html = render_html()           # 선택 "가": 결과 통째로 삽입

    today = datetime.date.today().isoformat()

    return f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>크립토 트렌드 뉴스레터</title></head>
<body style="font-family:'Malgun Gothic',sans-serif;background:#fff;padding:24px;max-width:760px;margin:0 auto;color:#222;">
  <h1 style="font-size:22px;color:#111;margin-bottom:2px;">🪙 크립토 중장기 트렌드 뉴스레터</h1>
  <div style="font-size:12px;color:#999;margin-bottom:8px;">{today} · 10년 보유 관점 · 트렌드 파악용</div>
  {_section_prices(prices)}
  {_section_indicators(fg, funding, stable, halving)}
  {bills_html}
  {_section_news(news)}
</body></html>'''


if __name__ == "__main__":
    html = build_html()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crypto_newsletter.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"생성 완료 → {out_path}")
