import os
import re
import requests
from playwright.sync_api import sync_playwright

URL = "https://portwatch-vi.xyz/"
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
SCREENSHOT_PATH = "portwatch_progress.png"


def fetch_progress_and_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        body_text = page.inner_text("body")
        matches = re.findall(r"\b\d{1,3}(?:\.\d+)?\s*%", body_text)
        progress_value = matches[0].replace(" ", "") if matches else None

        leader_info = ""
        for line in body_text.splitlines():
            line_clean = line.strip()
            if line_clean.lower().startswith("leader:"):
                leader_info = line_clean
                break

        page.screenshot(path=SCREENSHOT_PATH, full_page=False)
        browser.close()
        return progress_value, leader_info


def send_to_telegram(progress_value: str | None, leader_info: str):
    if not progress_value:
        caption = "לא הצלחתי לזהות אחוז התקדמות אוטומטית (מצורף צילום מסך)"
    else:
        caption = f"📊 *עדכון PortWatch VI*\nאחוז התקדמות נוכחי: *{progress_value}*"

    if leader_info:
        caption += f"\n🏆 {leader_info}"

    endpoint = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(SCREENSHOT_PATH, "rb") as photo:
        response = requests.post(
            endpoint,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "Markdown",
            },
            files={"photo": photo},
            timeout=30,
        )
    response.raise_for_status()


if __name__ == "__main__":
    value, leader = fetch_progress_and_screenshot()
    send_to_telegram(value, leader)
    print("נשלח לטלגרם:", value, leader)
