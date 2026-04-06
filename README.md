# ofo_auto_checkin

GitHub Actions daily auto check-in for OFO.

## Setup

1. Open the repository settings and add a GitHub Actions secret named `OFO_AUTH_DATA`.
2. Paste only the `auth_data` value into that secret, not the full URL.
3. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as GitHub Actions secrets.
4. Push this repository to GitHub and enable Actions.

## Schedule

- Runs every day at 09:00 Asia/Shanghai.
- Supports manual runs from the GitHub Actions page with `workflow_dispatch`.
- Sends a Telegram notification after every run, whether the check-in succeeds or fails.

## Local run

```bash
export OFO_AUTH_DATA='your_auth_data'
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'
python3 checkin.py
```
