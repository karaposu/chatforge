# Contribution 4: Progress Tracker

## What It Solves

When an agent runs a multi-step task (process 13 items, analyze
30 pages, fill 10 forms), the user sees nothing until it's done.
No progress bar, no "3 of 13 complete", no ETA. The UI is blank
for minutes.

Chatforge has no progress concept — its agents are single-turn.
This tracker gives any multi-step agent the ability to report
progress in real-time via the SSE stream.

## How It Works

```
Agent run starts
       │
  set_total(13)           ← "there are 13 items to process"
       │
  on_task_started("t1")   ← "starting item 1"
       │
  on_task_completed("t1") ← "item 1 done"
       │
  on_task_started("t2")   ← "starting item 2"
       │
  ...
       │
  to_dict()               ← snapshot for SSE chunk
       │                       {
       ▼                         "total": 13,
  SSE: {"type":"progress",       "completed": 5,
        "progress": {...}}       "failed": 0,
                                 "active": "t6",
                                 "percent": 38
                                }
The stream bridge emits {"type": "progress", "progress": ...}
chunks periodically. The frontend reads them to update a progress
bar.

## Design Decisions

**Task-ID based, not index-based** — works for any kind of task, not just numbered sequences
**No domain-specific phases** — the tracker doesn't know what "matching" or "filling" means. It just tracks started/done/failed.
**Thread-safe** — uses a lock for concurrent access (agent stream runs on a different thread or task than SSE reads)
**Snapshot via to_dict()** — returns a plain dict suitable for JSON serialization in SSE chunks
## Target Location in Chatforge

chatforge/services/progress.py
```

