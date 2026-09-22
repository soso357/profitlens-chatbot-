# Proposing new capabilities

Full process: docs/workflow.md, "Capability evolution".

- When you notice something worth improving that Ioseb did not ask for (a task repeated twice, a spec gap, a missing guardrail or test, a mistake made twice), write it as a proposal with the propose-capability skill and mention it in one sentence. Do not build it.
- Build only proposals with `status: approved`. Skills are built with skill-creator, tested, then the proposal is set to `built`.
- Never install a third party plugin, skill or MCP server without approval and a code review of its hooks and scripts.
- Never let a new capability weaken a founder decision (docs/adr/0001 to 0006) or a rule R1 to R14.
