"""
send_email_crypto.py — 크립토 뉴스레터(index.html)를 Gmail로 첨부 발송
용도: daily.yml에서 build_newsletter.py 성공 후 자동 호출 (텔레그램 다음 스텝)
설계: krx-automation/send_email.py와 동일 패턴 (SMTP_SSL + 첨부)
환경변수: GMAIL_ADDRESS(또는 GMAIL_USER), GMAIL_APP_PASSWORD
  - GitHub Actions: Secrets → env로 주입
  - 로컬: .env 파일 있으면 로드 (python-dotenv 없으면 건너뜀)
"""

import os
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# 로컬 실행용 .env 로드 (Actions에서는 dotenv 없어도 무방 — Secrets가 env로 들어옴)
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

GMAIL_USER = os.getenv("GMAIL_ADDRESS") or os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")


def send_crypto_email(html_path=HTML_PATH, to=None):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise RuntimeError("GMAIL_ADDRESS(또는 GMAIL_USER) / GMAIL_APP_PASSWORD 환경변수가 없습니다.")

    if not os.path.exists(html_path):
        raise FileNotFoundError(f"HTML 파일 없음: {html_path}")

    to = to or GMAIL_USER  # 수신자 미지정 시 자기 자신에게 발송
    today = datetime.datetime.now().strftime("%Y%m%d")
    subject = f"크립토 트렌드 뉴스레터 {today}"

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(
        f"{subject} 첨부파일을 확인하세요.\n"
        "웹 버전: https://hyunseokyang01-hue.github.io/crypto-dashboard/",
        "plain", "utf-8"))

    with open(html_path, "rb") as f:
        part = MIMEBase("text", "html")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    # RFC 5987: 한글 파일명을 utf-8 charset parameter로 전달
    part.add_header(
        "Content-Disposition",
        "attachment",
        filename=("utf-8", "", f"크립토_뉴스레터_{today}.html"),
    )
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, to, msg.as_string())

    print(f"[이메일] 발송 완료 → {to} / 제목: {subject}")


if __name__ == "__main__":
    send_crypto_email()
