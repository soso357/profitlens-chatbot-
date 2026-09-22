# Build log

One line per decision or notable event, newest last. Date first. Design choices also get an ADR in docs/adr/.

- 2026-09-22: Project built on Mac at ~/Desktop/PROFITLENS-CHATBOT instead of the Windows D: drive path. Python 3.12.
- 2026-09-22: Phase 0 started. Folder, virtual environment, requirements.txt, .gitignore, .env.example and git created.
- 2026-09-22: Website text downloaded directly from useprofitlens.com instead of being pasted. content/approved-answers.md drafted from it; report figures, percentages and sample numbers left out on purpose.
- 2026-09-22: Confirmed by Ioseb: no payment ever happens through the chatbot. The chatbot only has conversations and schedules the intake call. No card details, no payment links; payment questions go to a founder.
- 2026-09-22: Development workflow set up (ADR 0008 to 0012): CLAUDE.md split into intent, spec, plan, ADRs and this log; memory layers, session summaries, context handoff and statusline added; four official Anthropic plugins installed at project scope.
