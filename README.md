# Jelena: the ProfitLens website chat

A guide for Sophie, Leli and Tamuna. Jelena answers visitors on useprofitlens.com using only your approved answers, asks the qualifying questions, takes intake call requests and hands everything else to you. A founder emails the visitor to set up each call (ADR 0032).

## Is she working?

Open https://profitlens-chat.onrender.com/health

You should see `"status":"ok"`, what she has spent today and the daily limit, and `"telegram":"ok"` and `"email":"ok"`. If a page does not load at all, wait one minute and try again: on the free plan she sleeps when nobody chats and takes about a minute to wake up.

## Where you see chats and leads

1. **Telegram group:** every visitor message and every reply, as it happens.
2. **Email:** one email for each lead, intake call request, or question she hands to you. It includes the whole chat.

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

## Setting up the call

She no longer offers call times or books the calendar (ADR 0032). When a visitor gives their name, restaurant, state and email, you get the alert and email them to set up the 15 to 20 minute call yourself.

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
