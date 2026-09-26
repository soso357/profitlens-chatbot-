---
title: Post-deploy smoke check for Render
status: proposed
kind: test
source: 2026-09-26-919cea64.md
created: 2026-09-26
---

## Why
Multiple live bugs (session loss on restart, Telegram alerts failing, buying phrases not recognized) were only caught through manual live testing after each Render deploy, not by the offline checks that already passed.

## What
A short automated script run after each deploy that sends one test message through the live endpoint and confirms a reply, a lead is saved, and a Telegram alert arrives, before Ioseb is told a fix is live.

## Decision
(pending Ioseb)
