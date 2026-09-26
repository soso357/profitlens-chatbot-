---
last_verified: 2026-09-26
title: Glossary of technical terms explained to Ioseb
---

# Glossary

CLAUDE.md requires every technical term to be explained in one plain sentence the first time. Terms listed here have been explained already; reuse these wordings. Add new terms as they come up.

- **ADR (Architecture Decision Record)**: a short file recording one decision, the options, and why we chose one.
- **API**: a way for one program to ask another program to do something, like our service asking Claude for a reply.
- **API key**: a password that lets our service use a paid API; it lives only in environment variables.
- **Compaction**: Claude Code squeezing a long conversation into a summary so it can keep going.
- **Context window**: how much conversation Claude can hold in mind at once; the statusline shows how full it is.
- **CORS**: a browser rule that lets our service accept chat messages only from our own website.
- **Environment variable**: a setting stored on the computer or server, outside the code, used for secrets.
- **FastAPI**: the Python toolkit we use to build the chat service.
- **Git / commit**: the project's history; a commit is one saved step you can always go back to.
- **Hook**: a small script Claude Code runs automatically when something happens (session starts, a file is edited).
- **Plugin**: a package that adds skills, hooks or tools to Claude Code.
- **Render**: the hosting company that will run the chat service on the internet.
- **Service account**: a robot Google account our service uses to read and write the booking calendar.
- **Skill**: a written procedure Claude Code loads when a task needs it, like a checklist.
- **SMTP**: the standard way a program sends email (we use Zoho's).
- **SQLite**: a whole database kept in a single file on disk.
- **Statusline**: the line at the bottom of Claude Code showing model, context use and warnings.
- **Virtual environment (.venv)**: a private folder of Python libraries just for this project.
