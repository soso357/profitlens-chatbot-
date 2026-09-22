# Review policy

Used by Claude when reviewing changes (/code-review, security-guidance) before a phase gate or a commit. Report Important findings separately from Nits.

## Important (must fix before the phase gate)
1. Anything that lets the chatbot say something not in content/approved-answers.md, state a figure, make a promise, or pretend to be human (R1 to R3).
2. A guardrail enforced only in the prompt and not in code (spec section 4).
3. A secret in code, logs, git or an error message (R7). Visitor data outside the server or kept past 30 days (R9).
4. Missing or bypassable rate limit, token cap, spend cap or kill switch (R8, G4 to G6).
5. CORS wider than useprofitlens.com and the Render URL (G7).
6. A visitor left without a path when something fails (B11).
7. A new library not approved (R10).
8. A requirement id in the spec with no test.

## Nits (mention, do not block)
Naming, comments, small duplication, style.

## Skip
.venv/, memory/episodic/ (generated), docs/research/.
