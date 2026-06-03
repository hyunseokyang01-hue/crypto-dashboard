"""
crypto_news.py — 암호화폐 뉴스 헤드라인 수집 (Step A-2)
용도: run_crypto_daily.py에서 호출 → 헤드라인 반환 → HTML/메일로 전달
설계: crypto_fetch.py와 동일 (순수 수집 함수만. 저장·발송 없음)
소스: Google News RSS (무료, 키 불필요). 표준 라이브러리만 사용.
"""
import requests
import urllib.parse
import datetime
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

# ── 추적 키워드 (항목별) ──────────────────
KEYWORDS = {
    "법률":   ["CLARITY Act", "crypto regulation", "stablecoin bill", "MiCA", "crypto tax"],
    "기술":   ["RWA tokenization", "quantum computing bitcoin", "STO", "tokenized treasuries", "stablecoin payments"],
    "지정학": ["bitcoin strategic reserve", "bitcoin geopolitics", "CBDC", "dedollarization"],
}

# ── 언어별 Google News 설정 (hl, gl, ceid) ──
LANGS = {
    "한국어": ("ko", "KR", "KR:ko"),
    "영어":   ("en-US", "US", "US:en"),
    "일본어": ("ja", "JP", "JP:ja"),
}

PER_QUERY = 4    # (항목·언어)당 최신 헤드라인 수 (필터 후 기준)
RECENT_DAYS = 7  # 최근 N일 이내 기사만 (매일 발송용)
TIMEOUT = 10
HEADERS = {"User-Agent": "Mozilla/5.0"}  # Google News RSS는 UA 없으면 거부될 수 있음


def _is_recent(pub_date_str, days=RECENT_DAYS):
    """pubDate 문자열이 오늘 기준 N일 이내면 True. 파싱 실패 시 False(제외)."""
    if not pub_date_str:
        return False
    try:
        pub = parsedate_to_datetime(pub_date_str)
    except (TypeError, ValueError):
        return False
    now = datetime.datetime.now(datetime.timezone.utc)
    return (now - pub).days < days


def _fetch_one(query, lang_cfg, limit=PER_QUERY):
    """단일 (키워드묶음 × 언어) RSS 호출 → 최근 기사만 limit개 반환."""
    hl, gl, ceid = lang_cfg
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    items = []
    for item in root.findall(".//item"):
        pub = item.findtext("pubDate")
        if not _is_recent(pub):       # 7일 필터: 슬라이스 전에 먼저 거름
            continue
        items.append({
            "제목": item.findtext("title"),
            "링크": item.findtext("link"),
            "발행일": pub,
            "출처": item.findtext("source"),
        })
        if len(items) >= limit:
            break
    return items


def fetch_news(keywords=KEYWORDS, langs=LANGS):
    """전체 뉴스 수집 — 왜: 법률·기술·지정학 중장기 내러티브 추적.
    항목별 키워드를 OR로 묶어 언어별로 수집. (항목 × 언어) = 9회 호출."""
    out = []
    seen = set()  # 링크 중복 제거
    for category, words in keywords.items():
        query = " OR ".join(words)
        for lang_name, lang_cfg in langs.items():
            for art in _fetch_one(query, lang_cfg):
                if art["링크"] in seen:
                    continue
                seen.add(art["링크"])
                art["분류"] = category
                art["언어"] = lang_name
                out.append(art)
    return out


if __name__ == "__main__":
    news = fetch_news()
    print(f"=== 총 {len(news)}건 수집 (최근 {RECENT_DAYS}일) ===\n")
    for n in news:
        print(f"[{n['분류']}/{n['언어']}] {n['제목']}")
        print(f"    {n['출처']} | {n['발행일']}")
