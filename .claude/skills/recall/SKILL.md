---
name: recall
description: Search the project's memory (past session summaries, ADRs, proposals, lessons, docs, content) for what was decided or done before. Use when the user refers to earlier work ("like last time", "what did we decide about..."), before re-deciding something, or when unsure whether something was already tried.
---

# Recall

```
python3 .claude/scripts/memory_index.py search <words>
python3 .claude/scripts/memory_index.py recent 5
python3 .claude/scripts/memory_index.py proposals
```

Open the files the search returns and read the relevant part. Quote the file path when you tell the user what was found. If memory and the current code disagree, the code and git history win; fix the memory file.
