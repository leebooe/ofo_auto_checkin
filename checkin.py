#!/usr/bin/env python3
import json
import os
import sys
from typing import Tuple
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = "https://ofotw.org/api/v1/user/checkin/do"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://ofotw.org",
    "Referer": "https://ofotw.org/",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "X-Requested-With": "XMLHttpRequest",
}


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_payload(raw_body: str) -> dict:
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        fail(f"Received non-JSON response: {raw_body}")


def send_telegram_message(message: str) -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        fail(
            "Missing required Telegram environment variables: "
            "TELEGRAM_BOT_TOKEN and/or TELEGRAM_CHAT_ID"
        )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    body = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": message,
        }
    ).encode("utf-8")
    request = urllib.request.Request(url=url, data=body, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        fail(f"Telegram notification failed with HTTP {exc.code}: {body}")
    except urllib.error.URLError as exc:
        fail(f"Telegram notification request failed: {exc}")

    payload = parse_payload(raw_body)
    if not payload.get("ok"):
        fail(f"Telegram notification failed: {raw_body}")


def run_checkin() -> Tuple[bool, str]:
    auth_data = os.getenv("OFO_AUTH_DATA")
    if not auth_data:
        raise RuntimeError("Missing required environment variable: OFO_AUTH_DATA")

    url = f"{BASE_URL}?{urllib.parse.urlencode({'auth_data': auth_data})}"
    request = urllib.request.Request(url=url, method="POST", headers=HEADERS)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status_code = response.status
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        payload = parse_payload(body)
        message = payload.get("message", "")

        # The API returns HTTP 500 when the user has already checked in today.
        if exc.code == 500 and "已经签到过了" in message:
            return True, "\n".join(
                [
                    "OFO 签到结果: 今天已经签到过了",
                    "traffic_reward=0",
                    "days_reward=0",
                ]
            )

        raise RuntimeError(f"Check-in failed with HTTP {exc.code}: {body}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Check-in request failed: {exc}")

    payload = parse_payload(raw_body)
    data = payload.get("data") or {}
    message = data.get("message", "No message returned")
    traffic_reward = data.get("traffic_reward", 0)
    days_reward = data.get("days_reward", 0)

    return True, "\n".join(
        [
            "OFO 签到结果: 成功",
            f"http_status={status_code}",
            f"message={message}",
            f"traffic_reward={traffic_reward}",
            f"days_reward={days_reward}",
        ]
    )


def main() -> None:
    github_repository = os.getenv("GITHUB_REPOSITORY", "local")
    github_run_id = os.getenv("GITHUB_RUN_ID")
    run_url = ""
    if github_run_id:
        run_url = (
            f"https://github.com/{github_repository}/actions/runs/{github_run_id}"
        )

    try:
        success, result_message = run_checkin()
    except Exception as exc:
        success = False
        result_message = f"OFO 签到结果: 失败\nerror={exc}"

    notification_lines = [result_message, f"repository={github_repository}"]
    if run_url:
        notification_lines.append(f"run_url={run_url}")
    notification_message = "\n".join(notification_lines)

    print(notification_message)
    send_telegram_message(notification_message)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
