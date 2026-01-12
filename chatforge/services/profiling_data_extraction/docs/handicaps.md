# Profile Miner Handicaps & Design Issues



## 1. Sender Attribution

### The Problem
In multi-party conversations, extracted facts need attribution:
- "I'm 28 years old" - WHO is 28?
- Without sender tracking, profiles get mixed

### The Solution
For MVP, assume single-speaker extraction:
- Filter messages by sender_id before processing
- Extract profile for one person at a time
- Multi-party handling is a future enhancement



## 2. 

ProfilerMessage is a one messages and we have list of them. but context is important, for example lets say that only one ProfilerMessage
  exists in input of extract_core_identity and it's content is \
  \
  "it was really bad food"\
  \
  if we take this message by itself we are missing what it refers to. so we need to take the previous messages. that was the point of context
  messages.  but then when do we do extraction our prompt must differantiate the context messgaes and the target message...\






