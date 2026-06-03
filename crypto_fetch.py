"""
crypto_fetch.py — 암호화폐 중장기(10년) 트렌드 지표 수집 (Step A)
용도: run_crypto_daily.py에서 호출 → 결과 반환 → HTML/메일로 전달
설계: step1_fetch.py와 동일 역할 (순수 수집 함수만. 저장·발송 로직 없음)
실패 시 예외를 그대로 raise → 상위 오케스트레이터에서 재시도/스킵 판단
"""
import requests
import datetime

# ── 설정 ─────────────────────────────────
VS_CURRENCY = "krw"                        # 달러 기준이면 "usd"
COIN_IDS = ["bitcoin", "ethereum"]         # CoinGecko 코인 id. 추가는 여기에
FUNDING_SYMBOLS = ["BTCUSDT", "ETHUSDT"]   # Binance 선물 심볼
NEXT_HALVING_DATE = datetime.date(2028, 4, 20)  # [추정] 다음 반감기
TIMEOUT = 10


def fetch_prices(coin_ids=COIN_IDS, vs=VS_CURRENCY):
    """시세·변동성 — 왜: 모든 판단의 기준선. 7일/30일 변동률로 추세 확인. CoinGecko 공개 API."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": vs, "ids": ",".join(coin_ids),
              "price_change_percentage": "24h,7d,30d"}
    r = requests.get(url, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for c in r.json():
        out.append({
            "코인": c["symbol"].upper(),
            "현재가": c["current_price"],
            "24h%": c.get("price_change_percentage_24h_in_currency"),
            "7d%": c.get("price_change_percentage_7d_in_currency"),
            "30d%": c.get("price_change_percentage_30d_in_currency"),
            "전고점대비%": c.get("ath_change_percentage"),
        })
    return out


def fetch_fear_greed():
    """공포탐욕지수 — 왜: 극단 공포=누적, 극단 탐욕=분산 신호. alternative.me 공개 API."""
    r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=TIMEOUT)
    r.raise_for_status()
    d = r.json()["data"][0]
    return {"값": int(d["value"]), "분류": d["value_classification"]}


def fetch_stablecoin_mcap():
    """스테이블코인 시총 — 왜: 시장 대기 매수 유동성 프록시. 증가=유입 추세. DeFiLlama 공개 API."""
    r = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=TIMEOUT)
    r.raise_for_status()
    last = r.json()[-1]
    total = last["totalCirculating"]["peggedUSD"]
    return {"총시총_USD": total}


def fetch_funding_rates(symbols=FUNDING_SYMBOLS):
    """펀딩비(참고용) — 왜: 양수=롱 과열, 음수=숏 과열. 장기엔 참고만. Binance 선물 공개 API."""
    out = []
    for sym in symbols:
        r = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex",
                         params={"symbol": sym}, timeout=TIMEOUT)
        r.raise_for_status()
        d = r.json()
        out.append({"심볼": sym, "펀딩비%": float(d["lastFundingRate"]) * 100})
    return out


def halving_countdown(target=NEXT_HALVING_DATE):
    """반감기 D-day — 왜: 4년 주기. 중장기 사이클 위치 앵커. [추정일 기준]"""
    return {"다음반감기_추정": target.isoformat(),
            "D-day": (target - datetime.date.today()).days}


if __name__ == "__main__":
    import json
    print("=== 시세·변동성 ==="); print(json.dumps(fetch_prices(), ensure_ascii=False, indent=2))
    print("=== 공포탐욕지수 ==="); print(fetch_fear_greed())
    print("=== 스테이블코인 시총 ==="); print(fetch_stablecoin_mcap())
    print("=== 펀딩비 ==="); print(fetch_funding_rates())
    print("=== 반감기 D-day ==="); print(halving_countdown())
