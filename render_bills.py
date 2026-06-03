"""
render_bills.py — crypto_bills.json을 읽어 법안 타임라인 HTML 생성
용도: 단독 실행으로 crypto_bills.html 확인 → 나중에 뉴스레터 본문에 삽입
설계: update_html.py와 동일 역할 (데이터 읽어 HTML 생성. 수집·발송 없음)
"""
import json
import os

STATUS_STYLE = {
    "done":        ("#2f8f5b", "완료",   "1"),      # 채운 초록
    "in_progress": ("#d9a441", "진행중", "0.55"),   # 진행 노랑(반투명)
    "pending":     ("#cfd3d8", "예정",   "0.25"),   # 흐린 회색
}


def _bar(stage):
    color, label, opacity = STATUS_STYLE.get(stage["status"], ("#cfd3d8", "?", "0.25"))
    return f'''
    <div style="display:flex;align-items:center;margin:6px 0;font-size:13px;">
      <div style="width:170px;color:#333;">{stage['stage']}</div>
      <div style="flex:1;background:#f0f1f3;border-radius:4px;height:22px;position:relative;">
        <div style="width:100%;height:100%;background:{color};opacity:{opacity};border-radius:4px;"></div>
      </div>
      <div style="width:90px;text-align:right;color:#666;font-size:11px;">{stage['date']}</div>
      <div style="width:54px;text-align:right;color:{color};font-size:11px;font-weight:600;">{label}</div>
    </div>'''


def render_html(json_path="crypto_bills.json"):
    with open(json_path, encoding="utf-8-sig") as f:
        data = json.load(f)

    blocks = []
    for bill_name, info in data.items():
        if bill_name.startswith("_"):   # _읽는법 같은 메타키 건너뜀
            continue
        rows = "".join(_bar(s) for s in info["stages"])
        blocks.append(f'''
        <div style="margin-bottom:28px;">
          <div style="font-size:16px;font-weight:700;color:#111;">{bill_name}</div>
          <div style="font-size:12px;color:#888;margin-bottom:10px;">{info.get("설명","")}</div>
          {rows}
        </div>''')

    html = f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>법안 타임라인</title></head>
<body style="font-family:'Malgun Gothic',sans-serif;background:#fff;padding:24px;max-width:760px;">
  <h2 style="font-size:18px;color:#111;border-bottom:2px solid #111;padding-bottom:8px;">
    📋 가상자산 법안 진척 타임라인</h2>
  <div style="font-size:11px;color:#999;margin-bottom:20px;">
    완료 = 채운 막대 · 진행중 = 노랑 · 예정 = 흐린 막대 &nbsp;|&nbsp; 일부 단계는 추정</div>
  {"".join(blocks)}
</body></html>'''
    return html


if __name__ == "__main__":
    html = render_html()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crypto_bills.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"생성 완료 → {out_path}")
