# Privacy policy addition: the website chat

For the founders. Paste the section below into the privacy policy on useprofitlens.com, then publish. This meets rule R9 in docs/spec.md. It is a plain draft, not legal advice.

Before publishing, fill the two places marked FOUNDERS DECIDE.

---

## Our website chat

Our website has a chat assistant. It is run by AI (Claude, made by Anthropic), not by a person. It answers questions about ProfitLens and can book an intake call with us. If it cannot help, it passes your question to one of the founders by email.

**What we collect in the chat**

- What you type in the chat.
- If you book a call or ask us to follow up: your first name, your restaurant's name, your state and your email address.
- The time of the call you book.

We do not use cookies for the chat. Your browser keeps the conversation only for your visit, in that browser tab. Closing the tab clears it.

**How we use it**

- To answer your questions and book your call.
- To send the founders a copy of the conversation so they can follow up and check the assistant's answers.
- To email you about the call you booked. Google Calendar sends you the invitation.

We do not sell your information and do not use it for advertising.

**Who handles it for us**

- Anthropic, to run the AI assistant.
- Render, which hosts the chat.
- Google (Calendar and Gmail), for bookings and our email.
- Telegram, where the founders get a live copy of conversations.

**How long we keep it**

- Chat conversations on our server: deleted automatically after 30 days.
- Copies the founders receive in Telegram: deleted by hand after 30 days.
- Copies in our email: FOUNDERS DECIDE (for example, deleted after 30 days).
- Your name, restaurant, state and email if you booked or asked for follow up: FOUNDERS DECIDE (for example, until you ask us to delete them).

**Your choices**

You do not have to use the chat. You can email us instead. To see, correct or delete what you shared in the chat, email us at [your contact email].

---

## Facts this text is based on

| Statement | Source |
|---|---|
| 30 day deletion on the server | docs/spec.md section 5, ADR 0027 |
| Four contact details | ADR 0029 |
| Telegram copy, deleted by hand after 30 days | docs/spec.md section 5, ADR 0019 |
| Email copies, no retention set yet | ADR 0027 consequences (open question) |
| No cookies, sessionStorage for the visit only | app/static/widget.js |
| Anthropic, Render, Google, Telegram | docs/spec.md section 6 |
