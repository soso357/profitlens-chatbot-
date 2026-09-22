# Build log

One line per decision or notable event, newest last. Date first. Design choices also get an ADR in docs/adr/.

- 2026-09-22: Project built on Mac at ~/Desktop/PROFITLENS-CHATBOT instead of the Windows D: drive path. Python 3.12.
- 2026-09-22: Phase 0 started. Folder, virtual environment, requirements.txt, .gitignore, .env.example and git created.
- 2026-09-22: Website text downloaded directly from useprofitlens.com instead of being pasted. content/approved-answers.md drafted from it; report figures, percentages and sample numbers left out on purpose.
- 2026-09-22: Confirmed by Ioseb: no payment ever happens through the chatbot. The chatbot only has conversations and schedules the intake call. No card details, no payment links; payment questions go to a founder.
- 2026-09-22: ioseb@useprofitlens.com is the booking calendar, the notification recipient and the Zoho sending address. Calls bookable all 7 days, 19:00 to 03:00 Georgia time (Asia/Tbilisi, no daylight saving). Stored as non-secret settings in .env.example.
- 2026-09-22: Phase 0 approved. Phase 1 model chosen by Ioseb: Claude Haiku 4.5 (claude-haiku-4-5), about $0.03 per conversation. Sonnet 5 (about $0.05) was the recommended alternative for stricter rule following; revisit if Haiku slips in testing (ADR 0013).
- 2026-09-22: Development workflow set up (ADR 0008 to 0012): CLAUDE.md split into intent, spec, plan, ADRs and this log; memory layers, session summaries, context handoff and statusline added; four official Anthropic plugins installed at project scope.
- 2026-09-22: Telegram added for founder alerts (decided by Ioseb). Every lead, booking and handoff goes to a founders' Telegram chat AND by Zoho email (email is the record and backup). Alerts only: founders do not reply to visitors from Telegram. Visitors still chat only on the website. Visitor confirmations stay on email. Telegram is called over plain HTTPS, no new library. Built in Phase 2 (ADR 0014).
