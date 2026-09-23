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
- 2026-09-23: Obsidian map: .claude/scripts/obsidian_map.py rebuilds START HERE in the vault at every session start so every project note and code file is linked (none unconnected in the graph).
- 2026-09-23: tests/preview_chat.py added: try the chatbot before the API key exists (real prompt and guardrails, Haiku via the local Claude Code login). First preview: facts, prices and the savings handoff correct; replies sometimes run past 4 sentences and end with sales-style pushes.
- 2026-09-23: Ioseb chose to build Phase 3 (booking inside the chat, clickable times) now, before Phases 1 and 2 are approved.
- 2026-09-23: Booking inside the chat built (app/chat_booking.py, POST /book, time buttons on /test-chat, 1/2/3 in tests/preview_chat.py). Model signals with a hidden block; only code offers times and books. 19 offline checks pass; real run offered 3 calendar times in the visitor's zone.
- 2026-09-23: Every conversation goes to the founders' Telegram group after 30 quiet minutes (Ioseb, ADR 0015). Founders clear Telegram messages older than 30 days by hand. Phase 2 build started.
- 2026-09-23: Phase 2 built: leads.csv (every lead, fit or not), lead and handoff alerts by Telegram and email with the conversation, every conversation to Telegram after 30 quiet minutes. Found and fixed in testing: the model filled in an email the visitor never typed; code now accepts only emails the visitor typed. 32 offline checks pass; 3 preview conversations gave 3 correct leads.
