# Jelena: the ProfitLens website chat

A guide for Sophie, Leli and Tamuna. Jelena answers visitors on useprofitlens.com using only your approved answers, asks the qualifying questions, books intake calls in Google Calendar and hands everything else to you.

## Is she working?

Open https://profitlens-chat.onrender.com/health

You should see `"status":"ok"`, what she has spent today and the daily limit, and `"telegram":"ok"` and `"email":"ok"`. If a page does not load at all, wait one minute and try again: on the free plan she sleeps when nobody chats and takes about a minute to wake up.

## Where you see chats and leads

1. **Telegram group:** every visitor message and every reply, as it happens.
2. **Email:** one email for each lead, booking, or question she hands to you. It includes the whole chat.
3. **Google Calendar:** every booked intake call, with a Meet link. Google sends the invite to the visitor.

Please delete Telegram messages older than 30 days once a month (privacy promise).

## Change what she says

Everything she knows is in three files in the `content` folder on GitHub (https://github.com/soso357/profitlens-chatbot-):

1. `approved-answers.md`: the only things she may say.
2. `qualifying-questions.md`: the questions she asks.
3. `handoff-rules.md`: when she stops and passes the visitor to you.

To change one:

1. Open the file on GitHub and click the pencil icon.
2. Edit the text. Keep it short. No figures from reports, no promises.
3. Click **Commit changes**, then **Propose changes**, then **Create pull request**.
4. Wait for the green tick (automatic checks), then click **Merge**.
5. About 2 minutes later Jelena uses the new text.

If you are unsure, send the change to Ioseb instead.

## Change the call hours

On Render (https://dashboard.render.com), open **profitlens-chat**, then **Environment**. Change the setting, click **Save**; she restarts in about 2 minutes.

| Setting | Now | Meaning |
|---|---|---|
| BOOKING_TIMEZONE | Asia/Tbilisi | Your time zone |
| BOOKING_DAYS | mon,tue,wed,thu,fri,sat,sun | Days calls can be booked |
| BOOKING_START | 19:00 | First call time |
| BOOKING_END | 03:00 | Last call ends (after midnight is fine) |
| CALL_MINUTES | 20 | Call length |
| BOOKING_MIN_NOTICE_HOURS | 12 | Earliest booking from now |
| BOOKING_HORIZON_DAYS | 14 | How far ahead visitors can book |

She never offers a time that is already busy in the calendar.

## Turn her off in an emergency

A one click kill switch is not built yet. Until then:

1. **Fastest:** on Render, open **profitlens-chat**, then **Settings**, then **Suspend Web Service**. The chat bubble stops working at once. **Resume** turns her back on.
2. **Remove her from the site:** in Framer, delete the chat line from Custom Code and publish.

## Costs

1. **Claude (Anthropic):** she stops at $5 a day (setting DAILY_SPEND_LIMIT_USD on Render) and then shows visitors a "leave your email" form instead. So the most she can cost is about $150 a month; a normal day costs far less. Today's spend is on the health page.
2. **Render:** free now. The free plan loses the saved lead list and chat log each time she restarts (your emails and Telegram keep everything). The paid plan (Starter, about $7 a month, plus a small disk, under $1 a month) fixes that. Check render.com/pricing for current prices.
3. **Google, Gmail, Telegram, GitHub:** free.

## Lead list

Every lead is also saved in a file called `leads.csv` on the server. On the free plan it is wiped on every restart and cannot be opened from the Render website. Rely on the lead emails until the paid plan is set up.

## Who to ask

Ioseb. Technical notes for him are in `docs/` (start with `docs/progress.md`).
