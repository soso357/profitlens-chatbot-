# ADR 0021: Alert failures are reported through the other channel

- Status: Accepted
- Date: 2026-09-26
- Decided by: Ioseb (option "other channel")

## Context

Founder alerts (leads, bookings, handoffs, live chat copies) go to Telegram and by email. Both have failed silently: the .env was missing once, and on 2026-09-25 the Telegram group became a supergroup with a new chat ID. The code threw the error away, so nobody knew until someone checked by hand (proposal 0013).

Options offered:
- Other channel: if Telegram fails, email the founders the reason and the fix; if email fails, post to Telegram; at most once an hour per channel; also shown on /health. Pro: someone finds out within minutes. Con: silent only if both break at once.
- Status page only: /health shows the failure. Pro: simplest. Con: nobody looks, which is how the last failure went unnoticed.
- Other channel plus a daily "alerts OK" message to Telegram. Pro: even a double failure gets noticed when the daily message stops. Con: one extra message a day.

## Decision

Other channel. app/alert_health.py records the last result and reason per channel. telegram.py and email_alerts.py keep the real reason (Telegram's own error text, including the new chat ID after a group upgrade; the Google error for email) and never put a token in it. At startup the service checks the settings, asks Telegram whether the chat exists (posts nothing) and checks the Google sign-in (sends nothing). /health shows ok, failing or unknown per channel, without reasons, because the page is public.

## Consequences

Easier: a broken channel is reported with the exact fix, for example the new TELEGRAM_CHAT_ID. Harder: on the free Render plan the service restarts after sleeping, and the once an hour limit starts again after each restart, so a lasting problem can send a warning at each wake up. If both channels fail, only /health shows it (proposal 0015's post deploy check reads /health). Cost: none.
