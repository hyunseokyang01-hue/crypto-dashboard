"""
send_telegram.py — 크립토 뉴스레터 요약을 텔레그램으로 발송
용도: build_newsletter.py 실행 후 호출 → 핵심 수치 + 뉴스 제목 + Pages 링크 발송
"""
import os
import datetime
import urllib.request
import json

import crypto_fetch
import crypto_news

PAGES_URL = "https://hyunseokyang01-hue.github.io/crypto-dashboard/"
MAX_LEN = 4000


def _get_env():
    token   = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 환경변수가 없습니다.")
    return token, chat_id


def _send_message(token, chat_id, text):
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _split(text, max_len=MAX_LEN):
    chunks = []
    while len(text) > max_len:
        cut = text.rfind("\n", 0, max_len)
        if cut == -1:
            cut = max_len
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    chunks.append(text)
    return chunks


def build_summary():
    today   = datetime.date.today().isoformat()
    prices  = crypto_fetch.fetch_prices()
    fg      = crypto_fetch.fetch_fear_greed()
    stable  = crypto_fetch.fetch_stablecoin_mcap()
    halving = crypto_fetch.halving_cycle()
    news    = crypto_news.fetch_news()

    lines = [
        f"🪙 <b>크립토 트렌드 뉴스레터</b> {today}",
        f"📊 <a href='{PAGES_URL}'>대시보드 보기</a>",
        "",
    ]

    lines.append("📈 <b>시세</b>")
    for c in prices:
        def fmt(v):
            if v is None: return "—"
            sign = "+" if v >= 0 else ""
            return f"{sign}{v:.1f}%"
        lines.append(
            f"  {c['코인']}  ${c['현재가']:,.0f}  "
            f"24h {fmt(c['24h%'])}  7d {fmt(c['7d%'])}  30d {fmt(c['30d%'])}"
        )

    lines.append("")
    lines.append(f"😨 <b>공포탐욕</b>  {fg['값']} ({fg['분류']})")

    stable_b = stable["총시총_USD"] / 1e9
    lines.append(f"💵 <b>스테이블 시총</b>  ${stable_b:,.1f}B")

    lines.append(
        f"⏳ <b>반감기</b>  D-{halving['D-day']} / "
        f"진행률 {halving['진행률%']}% / {halving['단계']}"
    )

    lines.append("")
    lines.append("📰 <b>뉴스 헤드라인</b>")
    seen_titles = set()
    cats = {}
    for n in news:
        title_key = n["제목"][:40] if n["제목"] else ""
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        cats.setdefault(n["분류"], []).append(n)

    for cat, arts in cats.items():
        lines.append(f"\n<b>[{cat}]</b>")
        for a in arts[:4]:
            lines.append(f"  • {a['제목']}")

    return "\n".join(lines)


def send_telegram():
    token, chat_id = _get_env()
    text = build_summary()
    chunks = _split(text)
    for i, chunk in enumerate(chunks):
        _send_message(token, chat_id, chunk)
        print(f"[텔레그램] {i+1}/{len(chunks)} 발송 완료")
    print(f"[텔레그램] 전체 발송 완료 (총 {len(chunks)}건)")


if __name__ == "__main__":
    send_telegram()