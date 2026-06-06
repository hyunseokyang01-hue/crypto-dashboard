$content = @'
"""
crypto_fetch.py — 암호화폐 중장기(10년) 트렌드 지표 수집 (Step A)
용도: run_crypto_daily.py에서 호출 → 결과 반환 → HTML/메일로 전달
설계: step1_fetch.py와 동일 역할 (순수 수집 함수만. 저장·발송 로직 없음)
실패 시 예외를 그대로 raise → 상위 오케스트레이터에서 재시도/스킵 판단
"""
import requests
import datetime
import yfinance as yf

VS_CURRENCY = "usd"
COIN_IDS = ["bitcoin", "ethereum"]
FUNDING_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
NEXT_HALVING_DATE = datetime.date(2028, 4, 20)
LAST_HALVING_DATE = datetime.date(2024, 4, 20)
STABLE_STOCKS = {"COIN": "코인베이스", "HOOD": "로빈후드", "CRCL": "써클"}
TIMEOUT = 10


def fetch_prices(coin_ids=COIN_IDS, vs=VS_CURRENCY):
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
    r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=TIMEOUT)
    r.raise_for_status()
    d = r.json()["data"][0]
    return {"값": int(d["value"]), "분류": d["value_classification"]}


def fetch_stablecoin_mcap():
    r = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=TIMEOUT)
    r.raise_for_status()
    last = r.json()[-1]
    total = last["totalCirculating"]["peggedUSD"]
    return {"총시총_USD": total}


def fetch_funding_rates(symbols=FUNDING_SYMBOLS):
    out = []
    for sym in symbols:
        r = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex",
                         params={"symbol": sym}, timeout=TIMEOUT)
        r.raise_for_status()
        d = r.json()
        out.append({"심볼": sym, "펀딩비%": float(d["lastFundingRate"]) * 100})
    return out


def halving_countdown(target=NEXT_HALVING_DATE):
    return {"다음반감기_추정": target.isoformat(),
            "D-day": (target - datetime.date.today()).days}


def fetch_price_series(coin_ids=COIN_IDS, vs=VS_CURRENCY, days=7):
    out = {}
    for cid in coin_ids:
        url = f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart"
        params = {"vs_currency": vs, "days": days, "interval": "daily"}
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        prices = r.json()["prices"]
        sym = "BTC" if cid == "bitcoin" else ("ETH" if cid == "ethereum" else cid.upper())
        out[sym] = {
            "날짜": [datetime.datetime.utcfromtimestamp(p[0]/1000).strftime("%m-%d") for p in prices],
            "가격": [round(p[1], 2) for p in prices],
        }
    return out


def fetch_fear_greed_series(limit=30):
    r = requests.get(f"https://api.alternative.me/fng/?limit={limit}", timeout=TIMEOUT)
    r.raise_for_status()
    data = list(reversed(r.json()["data"]))
    return {
        "날짜": [datetime.datetime.utcfromtimestamp(int(d["timestamp"])).strftime("%m-%d") for d in data],
        "값": [int(d["value"]) for d in data],
    }


def fetch_stablecoin_series(days=30):
    r = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=TIMEOUT)
    r.raise_for_status()
    hist = r.json()[-days:]
    return {
        "날짜": [datetime.datetime.utcfromtimestamp(int(h["date"])).strftime("%m-%d") for h in hist],
        "시총_B": [round(h["totalCirculating"]["peggedUSD"]/1e9, 1) for h in hist],
    }


def fetch_stable_stocks(stocks=STABLE_STOCKS):
    out = []
    for ticker, name in stocks.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d", auto_adjust=True).dropna(subset=["Close"])
            if len(hist) >= 2:
                prev, last = float(hist["Close"].iloc[-2]), float(hist["Close"].iloc[-1])
                chg = round((last - prev) / prev * 100, 2)
            elif len(hist) == 1:
                last, chg = float(hist["Close"].iloc[-1]), None
            else:
                last, chg = None, None
            out.append({"티커": ticker, "이름": name,
                        "현재가": round(last, 2) if last else None, "전일대비%": chg})
        except Exception as e:
            print(f"{ticker} 수집 실패: {e}")
            out.append({"티커": ticker, "이름": name, "현재가": None, "전일대비%": None})
    return out


def halving_cycle(last=LAST_HALVING_DATE, target=NEXT_HALVING_DATE):
    today = datetime.date.today()
    total = (target - last).days
    elapsed = (today - last).days
    pct = round(elapsed / total * 100, 1)
    if pct < 25:   stage = "반감기 직후 (축적기)"
    elif pct < 55: stage = "상승기"
    elif pct < 80: stage = "과열·고점 구간"
    else:          stage = "조정·바닥 구간"
    return {
        "지난반감기": last.isoformat(),
        "다음반감기_추정": target.isoformat(),
        "D-day": (target - today).days,
        "경과일": elapsed,
        "진행률%": pct,
        "단계": stage,
    }
'@
[System.IO.File]::WriteAllText("C:\Users\user\dev\crypto-dashboard\crypto_fetch.py", $content, [System.Text.Encoding]::UTF8)
