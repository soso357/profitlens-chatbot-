# Survey: Claude Code plugins and skills (AI Pulse Georgia list)

Date: 2026-09-22. Source: github.com/tornikebolokadze1-cyber/awesome-ai-pulse-georgia, category "Claude Code Plugins and Skills" (40 repos).
Method: every repo shallow cloned and inspected at file level: hook definitions (the code that would run automatically on this Mac), scripts, skill files, network calls, tests. One repo (virgiliojr93/book-to-skill) failed to clone and was not assessed.
Filter for this project: a small Python chat service, one non engineer owner, strict content guardrails, own memory system (ADR 0009 to 0012).
Outcome: ADR 0011. Installed: 4 official Anthropic plugins. Ideas borrowed: listed per repo.

## Installed

| Repo | What the code actually is | Why |
|---|---|---|
| anthropics/claude-plugins-official: **skill-creator** | Skill plus Python scripts: run_eval.py, run_loop.py, improve_description.py, grader/comparator agents, HTML eval viewer | Builds approved proposals into tested skills; measures trigger accuracy |
| same: **claude-md-management** | Skill claude-md-improver with quality criteria, /revise-claude-md command. No hooks | Keeps CLAUDE.md under one page as rules are added |
| same: **security-guidance** | Python hooks: pattern warnings on every edit (patterns.py), background Claude review on Stop and on git commit/push (asyncRewake), bootstraps claude_agent_sdk venv in ~/.claude/security | Catches leaked secrets, injection, unsafe code in the chat service. Cost: a small background review per reply |
| same: **pyright-lsp** | LSP config only; needs pyright binary (installed with npm) | Type errors in the Python service show up as Claude edits |

## Ideas borrowed, not installed

| Repo | What the code actually is | Borrowed | Not installed because |
|---|---|---|---|
| affaan-m/ECC | 900 skills, 350 agents, 24 Node hook scripts on every event (session-end.js parses the transcript JSONL; evaluate-session.js; continuous-learning-v2 "instincts" with confidence scores; suggest-compact.js; cost-tracker.js) | Transcript condensing for session summaries; "learned behaviour becomes a skill after review" | Hooks on every tool call, huge surface, competes with our memory |
| yeachan-heo/oh-my-claudecode | 4,000 JS/TS files; 26 hooks incl. pre-compact, project-memory-precompact, context-guard-stop (blocks stop at 75% context), wiki session start/end | PreCompact snapshot; context threshold warning; "never block context limit stops" safety rule | Compiled dist/ code runs on every prompt and tool call; hard to audit |
| gsd-build/get-shit-done | 1,000 JS files; statusline writes context metrics to a temp file that a PostToolUse hook reads (gsd-context-monitor.js, warning at 35% remaining); .planning/ state files; 67 commands | The statusline to hook bridge for context %, used in our statusline.py and context_guard.py | Its own planning system duplicates docs/plan.md |
| obra/superpowers | 15 skills (brainstorming, writing-plans, TDD, verification-before-completion, systematic-debugging); one SessionStart hook injecting its intro skill | "Verify before claiming done" is in our phase-gate skill | Not selected (option offered, declined) |
| mattpocock/skills | Markdown skills incl. handoff and claude-handoff (write a handoff doc, reference artifacts instead of duplicating, redact secrets, suggest skills) | Our handoff skill: reference paths, no secrets, no duplication | Personal TypeScript focus |
| github/spec-kit | Python CLI `specify` that scaffolds templates (constitution, spec, plan, tasks, checklist) and slash commands | Spec with stable ids, "clarify open questions" before plan | Its CLI and templates are heavier than our three file chain |
| bmad-code-org/BMAD-METHOD | 42 role skills (analyst, PM, architect...) plus Python validators | Separation of roles maps to playbook stages | Built for teams; too much ceremony for one person |
| tornikebolokadze1-cyber/claude-code-setup | install.sh copying 23 rule files and shell hooks into ~/.claude (audit log, blocks force push and DROP TABLE, secret pattern scan, file backups, metrics on Stop) | Handoff notes and docs/decisions idea; force push and hard reset denied in our permissions | Installs globally into ~/.claude, affects every project; many rules are for other languages |
| multica-ai/andrej-karpathy-skills | One 65 line CLAUDE.md: think first, simplicity, surgical changes, goal driven | Spirit is in REVIEW.md and plan notes | Not selected |
| DietrichGebert/ponytail | Skill forcing the simplest solution; benchmarks; MCP variant | YAGNI mindset for a small service | Overlaps; no need for a plugin |
| NVIDIA/SkillSpector | Python scanner (static rules, YARA, unicode confusables, optional LLM pass, OSV lookups) for skills before install | Run `skillspector scan <dir> --no-llm` before approving any third party skill (ADR 0011) | Tool to run on demand, not a plugin |
| anthropics/skills | Official example skills; skill-creator source | Skill format | skill-creator installed via plugin |
| addyosmani/agent-skills | 25 engineering skills incl. spec-driven-development, documentation-and-adrs, context-engineering; SDD cache hooks | ADR practice | Overlaps with our own skills |
| wshobson/agents | 185 plugins, 767 agent files | None needed | Far beyond scope |
| VoltAgent/awesome-claude-code-subagents | 179 subagent Markdown files, no code | None needed | We do not need subagents yet |
| alirezarezvani/claude-skills | 846 skills, 745 Python scripts across business domains | None needed | Scope and size |
| github/awesome-copilot | Copilot catalog: 440 skills, 229 agents, hooks, MCP config | None needed | Built for Copilot |
| anthropics/claude-plugins-community | Mirror of 4 community plugins | None needed | Not relevant |
| ayghri/i-have-adhd | SessionStart hook injecting "action first, concise" rules; eval scripts with a judge | Short answers are already a user preference | Would fight the "explain every term" rule |
| gvzdv/claudish-to-english | MessageDisplay hook rewrites every reply via a second LLM call (Anthropic or OpenAI API with your key) | Plain English is enforced by CLAUDE.md instead | Sends every reply to an external API, adds latency and cost |
| blader/humanizer, petergyang/no-ai-slop | Single SKILL.md each (plus packaging scripts): catalogues of AI writing patterns incl. em dashes | Candidate for the founders' README (Phase 5) | Only writing style; our lint hook covers dashes |
| phuryn/pm-skills | 9 plugins, 69 PM skills (discovery, strategy, GTM), no hooks | Could help Ioseb's marketing work, outside this repo | Not a build tool |
| tt-a1i/archify | Node app turning architecture descriptions into interactive diagrams | Possible for the founders' handover | Not needed now |
| openai/codex-plugin-cc | Node plugin delegating to the local Codex CLI (needs OpenAI account); Stop review gate hook | None | Second vendor, second account |
| mvanhorn/last30days-skill | Python research skill calling Reddit, X, YouTube, HN, needs several API keys | Could support marketing research | Not a build tool; many keys |
| Donchitos/Claude-Code-Game-Studios | 98 agents and 73 skills for game studios | None | Different domain |
| K-Dense-AI/scientific-agent-skills, Imbad0202/academic-research-skills | Large science and academic writing skill libraries with Python tooling | None | Different domain |
| mukul975/Anthropic-Cybersecurity-Skills | 818 security skills mapped to MITRE and NIST | None | security-guidance covers our needs |
| anthropics/defending-code-reference-harness | Python harness for autonomous vulnerability discovery | None | Research tool, not for a small service |
| kepano/obsidian-skills, remotion-dev/skills, czlonkowski/n8n-skills, QwenLM/Qwen-MM-Plugins, erekle1/georgian-payments-skills | Domain skills (Obsidian notes, Remotion video, n8n with a remote MCP server at api.n8n-mcp.com, Qwen multimodal, TBC and Bank of Georgia APIs) | None | Not used in this project (and ADR 0006 rules out payments) |
| titanwings/distilly | Python collectors (email, Feishu, DingTalk) building person profiles | None | Not relevant; personal data collection |
| microsoft/skill-recorder | Electron app recording screen actions into skills | Maybe later for founders' repeated tasks | Desktop app, not needed |
| virgiliojr93/book-to-skill | Clone failed | n/a | Not assessed |

## Integrations recommended (not plugins)

| Integration | When | Why |
|---|---|---|
| Google Calendar MCP (claude.ai connector, already configured in this account) | Phase 3 testing | Lets Claude check that test bookings really appeared, without opening a browser |
| Gmail MCP (already configured) | Phase 2 and 3 testing | Check notification and confirmation emails arrived. Production email still goes through Zoho SMTP (R10) |
| Playwright (official external plugin) | Phase 4 | Real browser screenshots of the widget at desktop and mobile widths for the phase gate |
| Render | Phase 5 | Deploy from git; use its dashboard, no plugin needed |
| GitHub (remote repository) | Before Phase 5 | Render deploys from a git remote; also a backup. gh CLI is not installed yet |
| Claude Code Review (managed) with REVIEW.md | Once the repo is on GitHub | Automatic review of every change against our Important list |
