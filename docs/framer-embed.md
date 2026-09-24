# Putting the chat on the website (Framer)

The whole chat window lives on our chat service. Framer only gets one short line, so the 5,000 character limit for Framer custom code is never a problem, and changes to the chat never need a Framer edit.

## The embed line

```html
<script src="https://profitlens-chat.onrender.com/widget.js" defer></script>
```

The service runs on Render at https://profitlens-chat.onrender.com (health check: https://profitlens-chat.onrender.com/health).

No breakpoint settings are needed in Framer: the widget sizes itself. On screens narrower than 480 pixels (phones) the chat opens full screen; on larger screens it opens as a panel in the bottom right corner.

## Step 1: hidden test page first (rule R11)

1. In Framer, add a new page, for example `/chat-test`. Do not link it from the menu.
2. Open the page settings (the gear next to the page name). Turn off "Show in search engines".
3. In the same page settings, find "Custom Code", "End of <body> tag", and paste the embed line.
4. Publish. Open useprofitlens.com/chat-test and try the chat. Only people who know the address can find it.
5. Founders test it there and say "approved" before step 2.

## Step 2: the whole site (after founder approval)

1. Framer, Site Settings, General, Custom Code, "End of <body> tag": paste the embed line.
2. Remove it from the test page (otherwise nothing breaks, the widget loads once, but keep it tidy).
3. Publish.

## Which websites may use the chat

The service answers only pages from the addresses in the Render setting ALLOWED_ORIGINS (default: https://useprofitlens.com and https://www.useprofitlens.com). To try the chat on a Framer preview address (for example something.framer.website), add that address to ALLOWED_ORIGINS in Render, separated by a comma.

## Trying it on this Mac before Render

```
cd ~/Desktop/PROFITLENS-CHATBOT
TEST_PAGES=1 MODEL_VIA_CLAUDE_CODE=1 .venv/bin/uvicorn app.main:app --port 8765
```

Then open http://localhost:8765/widget-test (desktop) or http://localhost:8765/widget-phone (phone size).
MODEL_VIA_CLAUDE_CODE=1 gets replies through the Claude Code login, so it works without the Anthropic key. Alerts and leads are marked LOCAL TEST. Booking a time books a real call in the calendar.
