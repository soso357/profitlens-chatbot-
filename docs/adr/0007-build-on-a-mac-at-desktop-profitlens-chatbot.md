# ADR 0007: Build on a Mac at ~/Desktop/PROFITLENS-CHATBOT

- Status: Accepted
- Date: 2026-09-22
- Decided by: Ioseb

## Context

The brief said D:\Thursday- business\profitlens-chat-agent (Windows) but the build runs on a Mac.

## Decision

Project lives at ~/Desktop/PROFITLENS-CHATBOT, Python 3.12.

## Consequences

Paths in scripts are relative to the project root so the repo also works elsewhere.
