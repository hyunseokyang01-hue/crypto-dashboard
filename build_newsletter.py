"""
build_newsletter.py v2 — USD 시세 + BTC/ETH 그래프 세로 배치 2배 크기 + 포인트 시세 표시
"""
import datetime, os, json
import crypto_fetch, crypto_news
from render_bills import render_html

H2  = "font-size:18px;color:#111;border-bottom:2px solid #111;padding-bottom:8px;margin-top:32px;"
WHY = "font-size:12px;color:#888;margin:6px 0 14px;"

def _pct(v):
    if v is None:
        return '<span style="color:#999;">—</span>'
    color = "#2f8f5b" if v >= 0 else "#c0392b"
    sign  = "+" if v >= 0 else ""
    return f'<span style="color:{color};font-weight:600;">{sign}{v:.2f}%</span>'

def _card(title, body, why):
    return f'''
    <div style="border:1px solid #e4e6e9;border-radius:8px;padding:14px 16px;margin:10px 0;">
      <div style="font-size:13px;color:#888;">{title}</div>
      <div style="font-size:17px;font-weight:700;color:#111;margin:4px 0;">{body}</div>
      <div style="font-size:11px;color:#aaa;">{why}</div>
    </div>'''

def _section_prices(prices, price_series, stable_stocks):
    rows = ""
    for c in prices:
        rows += f'''
        <tr>
          <td style="padding:8px 10px;font-weight:700;border-top:1px solid #eee;">{c["코인"]}</td>
          <td style="padding:8px 10px;text-align:right;border-top:1px solid #eee;">${c["현재가"]:,.2f}</td>
          <td style="padding:8px 10px;text-align:right;border-top:1px solid #eee;">{_pct(c["24h%"])}</td>
          <td style="padding:8px 10px;text-align:right;border-top:1px solid #eee;">{_pct(c["7d%"])}</td>
          <td style="padding:8px 10px;text-align:right;border-top:1px solid #eee;">{_pct(c["30d%"])}</td>
          <td style="padding:8px 10px;text-align:right;border-top:1px solid #eee;">{_pct(c["전고점대비%"])}</td>
        </tr>'''

    btc_data   = price_series.get("BTC", {})
    eth_data   = price_series.get("ETH", {})
    btc_labels = json.dumps(btc_data.get("날짜", []))
    btc_vals   = json.dumps(btc_data.get("가격", []))
    eth_labels = json.dumps(eth_data.get("날짜", []))
    eth_vals   = json.dumps(eth_data.get("가격", []))

    stock_rows = ""
    for s in stable_stocks:
        price_str = f"${s['현재가']:.2f}" if s["현재가"] else "—"
        stock_rows += f'''
        <tr>
          <td style="padding:6px 10px;border-top:1px solid #eee;">{s["티커"]}</td>
          <td style="padding:6px 10px;text-align:right;border-top:1px solid #eee;">{price_str}</td>
          <td style="padding:6px 10px;text-align:right;border-top:1px solid #eee;">{_pct(s["전일대비%"])}</td>
        </tr>'''

    return f'''
    <h2 style="{H2}">① 시세 · 변동성</h2>
    <div style="{WHY}">모든 판단의 기준선 — 7일/30일 추세로 지금 위치 확인</div>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <tr style="background:#f0f1f3;color:#555;font-size:12px;">
        <th style="padding:8px 10px;text-align:left;">코인</th>
        <th style="padding:8px 10px;text-align:right;">현재가(USD)</th>
        <th style="padding:8px 10px;text-align:right;">24h</th>
        <th style="padding:8px 10px;text-align:right;">7d</th>
        <th style="padding:8px 10px;text-align:right;">30d</th>
        <th style="padding:8px 10px;text-align:right;">전고점대비</th>
      </tr>
      {rows}
    </table>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <div style="margin-top:24px;">
      <canvas id="chartBTC" style="width:100%;height:300px;"></canvas>
    </div>
    <div style="margin-top:24px;">
      <canvas id="chartETH" style="width:100%;height:300px;"></canvas>
    </div>
    <script>
    const btcCfg = {{
      type: "line",
      data: {{
        labels: {btc_labels},
        datasets: [{{ label: "BTC (USD)", data: {btc_vals},
          borderColor: "#f7931a", backgroundColor: "rgba(247,147,26,0.08)",
          borderWidth: 2, pointRadius: 4, pointHoverRadius: 6, tension: 0.3 }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ display: true }},
          tooltip: {{ callbacks: {{ label: ctx => "$" + (ctx.parsed.y/1000).toFixed(1) + "K" }} }},
          datalabels: {{ display: false }}
        }},
        scales: {{
          y: {{ ticks: {{ callback: v => "$" + (v/1000).toFixed(1) + "K" }} }}
        }}
      }}
    }};
    const ethCfg = {{
      type: "line",
      data: {{
        labels: {eth_labels},
        datasets: [{{ label: "ETH (USD)", data: {eth_vals},
          borderColor: "#627eea", backgroundColor: "rgba(98,126,234,0.08)",
          borderWidth: 2, pointRadius: 4, pointHoverRadius: 6, tension: 0.3 }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ display: true }},
          tooltip: {{ callbacks: {{ label: ctx => "$" + (ctx.parsed.y/1000).toFixed(1) + "K" }} }}
        }},
        scales: {{
          y: {{ ticks: {{ callback: v => "$" + (v/1000).toFixed(1) + "K" }} }}
        }}
      }}
    }};

    // 포인트 위 시세 레이블 플러그인
    const labelPlugin = {{
      id: "pointLabels",
      afterDatasetsDraw(chart) {{
        const ctx = chart.ctx;
        chart.data.datasets.forEach((ds, di) => {{
          const meta = chart.getDatasetMeta(di);
          meta.data.forEach((pt, i) => {{
            const val = ds.data[i];
            if (val == null) return;
            const txt = "$" + (val/1000).toFixed(1) + "K";
            ctx.save();
            ctx.font = "bold 10px sans-serif";
            ctx.fillStyle = ds.borderColor;
            ctx.textAlign = "center";
            ctx.fillText(txt, pt.x, pt.y - 8);
            ctx.restore();
          }});
        }});
      }}
    }};

    new Chart(document.getElementById("chartBTC"), {{ ...btcCfg, plugins: [labelPlugin] }});
    new Chart(document.getElementById("chartETH"), {{ ...ethCfg, plugins: [labelPlugin] }});
    </script>

    <div style="margin-top:20px;">
      <div style="font-size:13px;font-weight:700;color:#555;margin-bottom:6px;">크립토 관련주</div>
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <tr style="background:#f0f1f3;color:#555;font-size:12px;">
          <th style="padding:6px 10px;text-align:left;">심볼</th>
          <th style="padding:6px 10px;text-align:right;">현재가(USD)</th>
          <th style="padding:6px 10px;text-align:right;">전일대비</th>
        </tr>
        {stock_rows}
      </table>
    </div>'''

def _section_indicators(fg, fg_series, funding, stable, stable_series):
    funding_body = " · ".join(f"{f['심볼']} {f['펀딩비%']:+.4f}%" for f in funding)
    stable_b = stable["총시총_USD"] / 1e9

    fg_labels = json.dumps(fg_series.get("날짜", []))
    fg_vals   = json.dumps(fg_series.get("값", []))
    st_labels = json.dumps(stable_series.get("날짜", []))
    st_vals   = json.dumps(stable_series.get("시총_B", []))

    cards = (
        _card("공포탐욕지수", f"{fg['값']} ({fg['분류']})", "극단 공포=누적 / 극단 탐욕=분산")
        + _card("펀딩비 (참고)", funding_body, "롱/숏 과열 — 장기엔 참고만")
        + _card("스테이블코인 시총", f"${stable_b:,.1f}B", "시장 대기 매수 유동성 프록시")
    )

    return f'''
    <h2 style="{H2}">② 시장 심리 · 유동성</h2>
    {cards}

    <div style="display:flex;gap:16px;margin-top:16px;">
      <div style="flex:1;"><canvas id="chartFG"></canvas></div>
      <div style="flex:1;"><canvas id="chartST"></canvas></div>
    </div>
    <script>
    new Chart(document.getElementById("chartFG"), {{
      type: "line",
      data: {{
        labels: {fg_labels},
        datasets: [{{ label: "공포탐욕 (30일)", data: {fg_vals},
          borderColor: "#e74c3c", backgroundColor: "rgba(231,76,60,0.08)",
          borderWidth: 2, pointRadius: 1, tension: 0.3 }}]
      }},
      options: {{ plugins: {{ legend: {{ display: true }} }}, scales: {{ y: {{ min: 0, max: 100 }} }} }}
    }});
    new Chart(document.getElementById("chartST"), {{
      type: "line",
      data: {{
        labels: {st_labels},
        datasets: [{{ label: "스테이블 시총 (B$)", data: {st_vals},
          borderColor: "#27ae60", backgroundColor: "rgba(39,174,96,0.08)",
          borderWidth: 2, pointRadius: 1, tension: 0.3 }}]
      }},
      options: {{ plugins: {{ legend: {{ display: true }} }} }}
    }});
    </script>'''

def _section_halving(halving_cycle):
    h = halving_cycle
    pct = h["진행률%"]
    bar_color = "#f7931a" if pct < 50 else "#e74c3c"
    return f'''
    <h2 style="{H2}">③ 반감기 사이클</h2>
    <div style="{WHY}">4년 주기 포지션 확인 — 지금 사이클 어디쯤?</div>
    <div style="background:#f8f8f8;border-radius:8px;padding:16px;margin-bottom:8px;">
      <div style="font-size:13px;color:#555;margin-bottom:8px;">사이클 진행률 {pct:.1f}%</div>
      <div style="background:#e0e0e0;border-radius:4px;height:12px;overflow:hidden;">
        <div style="background:{bar_color};width:{min(pct,100):.1f}%;height:100%;border-radius:4px;"></div>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:11px;color:#aaa;margin-top:4px;">
        <span>반감기</span><span>다음 반감기</span>
      </div>
    </div>
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:8px;">
      {_card("경과일", f"{h['경과일']}일", "")}
      {_card("D-day", f"D-{h['D-day']}  ({h['다음반감기_추정']})", "[추정]")}
      {_card("현재 단계", h["단계"], "")}
    </div>
    <div style="font-size:11px;color:#aaa;margin-top:8px;">⚠ 반감기 사이클은 과거 패턴 참고용. 미래 수익 보장 없음.</div>'''

def _section_news(news):
    seen_titles = set()
    deduped = []
    for n in news:
        title_key = n["제목"][:40] if n["제목"] else ""
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        deduped.append(n)

    cats = {}
    for n in deduped:
        cats.setdefault(n["분류"], []).append(n)
    blocks = ""
    for cat, arts in cats.items():
        items = ""
        for a in arts:
            src = a.get("출처") or ""
            items += f'''
            <li style="margin:7px 0;font-size:13px;line-height:1.4;">
              <a href="{a["링크"]}" style="color:#1a4ba8;text-decoration:none;">{a["제목"]}</a>
              <span style="color:#aaa;font-size:11px;"> · {src} · {a["언어"]}</span>
            </li>'''
        blocks += f'''
        <div style="margin-bottom:16px;">
          <div style="font-weight:700;color:#111;font-size:14px;margin-bottom:4px;">{cat}</div>
          <ul style="margin:0;padding-left:18px;">{items}</ul>
        </div>'''
    return f'''
    <h2 style="{H2}">⑤ 뉴스 헤드라인</h2>
    <div style="{WHY}">법률·기술·지정학 중장기 내러티브 (최근 7일)</div>
    {blocks}'''

def build_html():
    prices        = crypto_fetch.fetch_prices()
    price_series  = crypto_fetch.fetch_price_series()
    fg            = crypto_fetch.fetch_fear_greed()
    fg_series     = crypto_fetch.fetch_fear_greed_series()
    stable        = crypto_fetch.fetch_stablecoin_mcap()
    stable_series = crypto_fetch.fetch_stablecoin_series()
    funding       = crypto_fetch.fetch_funding_rates()
    halving_cyc   = crypto_fetch.halving_cycle()
    stable_stocks = crypto_fetch.fetch_stable_stocks()
    news          = crypto_news.fetch_news()
    bills_html    = render_html()

    today = datetime.date.today().isoformat()

    return f"""<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>크립토 트렌드 뉴스레터</title>
</head>
<body style="font-family:'Malgun Gothic',sans-serif;background:#fff;padding:24px;max-width:860px;margin:0 auto;color:#222;">
  <h1 style="font-size:22px;color:#111;margin-bottom:2px;">🪙 크립토 중장기 트렌드 뉴스레터</h1>
  <div style="font-size:12px;color:#999;margin-bottom:8px;">{today} · 10년 보유 관점 · 트렌드 파악용</div>
  {_section_prices(prices, price_series, stable_stocks)}
  {_section_indicators(fg, fg_series, funding, stable, stable_series)}
  {_section_halving(halving_cyc)}
  {bills_html}
  {_section_news(news)}
</body></html>"""

if __name__ == "__main__":
    html = build_html()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"생성 완료 → {out_path}")

