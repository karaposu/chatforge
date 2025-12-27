# Future Schema Improvements

High-level concepts for future chatforge schema additions.

---

## 1. Context Table

### Problem

When conversations get long, we use a rolling window + summarization to manage context. Currently:
- Context is recalculated on every request
- Summaries are generated but not persisted
- If same context is needed later, we recalculate (wasteful)

### Concept

Store computed context snapshots so they can be reused:

```
contexts
├── id
├── chat_id
├── context_type          ← 'summary', 'rolling_window', 'compressed'
├── content               ← The actual context/summary text
├── token_count           ← Tokens in this context
├── source_message_range  ← Which messages this covers (start_id, end_id)
├── created_at
├── expires_at            ← Optional TTL
├── metadata              ← Model used, compression ratio, etc.
```

### Use Cases

- **Resume conversation**: Load last saved context instead of reprocessing
- **Branch conversations**: Fork from a saved context point
- **Analytics**: Track context growth over time
- **Cost optimization**: Avoid redundant summarization calls

---

## 2. User Profiles Table

### Problem

Chatforge can learn about users through conversations:
- Preferences, interests, communication style
- Facts mentioned (name, job, location)
- Behavior patterns

Currently this information is lost or must be extracted repeatedly.

### Concept

Store extracted user profile data:

```
user_profiles
├── id
├── external_user_id      ← Reference to host app's user
├── profile_type          ← 'preferences', 'facts', 'behavior', 'full'
├── data                  ← JSON of extracted profile
├── confidence            ← How confident we are in this data
├── source_chat_ids       ← Which chats contributed to this
├── last_updated
├── metadata
```

### Use Cases

- **Personalization**: AI remembers user preferences across chats
- **Continuity**: "Last time you mentioned you work at X..."
- **Onboarding**: Build profile progressively over conversations
- **Cross-chat memory**: Information persists beyond single chat

### Considerations

- Privacy: Users should control what's stored
- Accuracy: Profile data may become stale
- Extraction: Need reliable way to extract facts from conversations

---

## Implementation Priority

| Table | Priority | Complexity | Value |
|-------|----------|------------|-------|
| `contexts` | Medium | Low | Cost savings, performance |
| `user_profiles` | High | Medium | Core differentiator for chatforge |

These will be designed in detail when the core schema (v2) is stable.
