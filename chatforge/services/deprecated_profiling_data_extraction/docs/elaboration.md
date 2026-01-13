# Profile Miner: System Architecture & Implementation Details

## System Overview

Profile Miner is a conversational profiling system that transforms unstructured chat conversations into structured, actionable intelligence. It operates as a data extraction pipeline that processes conversation histories through LLM-powered semantic understanding to extract multi-dimensional profiling data according to the CPF-7 framework.


and since profiling sth that might needed in different different speed i think optionally being able to use websocket connection to do the extraction makes sense as well. 

## Core Architecture

```
[Database/Source] → [ProfilingInput] → [Profile Miner Pipeline] → [Structured Output]
                         ↓                      ↓
                   ChatMessages           LLM Extraction Engine
                   + Config               (7 Dimension Processing)
```

## Input Structure

### ProfilingInput Dataclass

The system accepts input via a standardized `ProfilingInput` dataclass that encapsulates both the conversation data and extraction configuration:

```python
@dataclass
class ProfilingInput:
    chat_messages: ChatMessages  # Collection of messages to process
    config: Config               # Extraction configuration settings
```

### ChatMessages Field

The `ChatMessages` field contains a list of `ProfilerMessage` dataclass objects:

```python
@dataclass
class ProfilerMessage:
    message_id: str  # Unique identifier for tracking
    content: str  # The actual text content of the message
    timestamp: str  # When the message was sent (ISO format)
    sender_id: str  # Who sent the message
    sender_name: Optional[str] = None  # Display name of the sender
    sender_type: str = "user"  # user, assistant, system, etc.

# The ChatMessages type is a list of ProfilerMessage objects
ChatMessages = List[ProfilerMessage]
```

Example message instance:
```python
message = ProfilerMessage(
    message_id="msg_123456",
    content="Just started my new role at Microsoft. The Seattle weather is taking some getting used to!",
    timestamp="2024-01-15T10:30:00Z",
    sender_id="user_789",
    sender_name="Alex Chen",
    sender_type="user"
)
```

### Config Field

The `Config` field determines what dimensions to extract and granularity settings:

```python
{
    "dimensions": {
        # Simple boolean flags for which CPF-7 dimensions to enable
        "core_identity": true,
        "opinions_views": true,
        "preferences_patterns": true,
        "desires_needs": true,
        "life_narrative": false,  # Can be disabled for specific use cases
        "events": true,
        "entities": true
    },
    "batch_size": 50,  # Messages per LLM call (1 = per-message, >1 = batch)
    "context_window": 10,  # Surrounding past messages for context
    "deduplication": true,  # Remove duplicate messages (useful for re-exported data)
    "output_format": "json"  # json, yaml, or custom schema
}
```

## Processing Modes

Profile Miner's processing mode is determined by the `batch_size` configuration:

### Per-Message Processing (batch_size: 1)
- Each message is analyzed individually in real-time
- Extraction happens as messages arrive
- Lower latency, ideal for live conversations
- Results are incremental and can be aggregated over time
- Suitable for chatbots, live support, or streaming applications

### Batch Processing (batch_size > 1)
- Multiple messages are processed together (e.g., batch_size: 50)
- Better context understanding from surrounding messages
- More efficient LLM usage (fewer API calls)
- Higher accuracy for relationship and pattern detection
- Ideal for historical analysis or periodic profile updates

## Internal Data Extraction Pipeline

### Stage 1: Input Validation & Preprocessing

1. **Message Validation**: Verify all required fields are present
2. **Temporal Sorting**: Messages are always sorted chronologically by timestamp
3. **Deduplication**: Remove duplicate messages (if configured)
4. **Context Windowing**: Group messages with surrounding context

### Stage 2: Multi-Dimensional Extraction

The pipeline processes messages through each enabled dimension using specialized LLM prompts:

Core Identity Extraction

 Opinions & Views Analysis

 Preference Pattern Recognition

Desires & Needs Identification

 Life Narrative Construction

 Event Detection

 Entity & Relationship Mapping



### Stage 3: Output Generation

The structured output is returned as a `ProfilingDataExtractionOutput` dataclass that provides granular visibility into what was extracted from each message and dimension:

## Output Structure

### ProfilingDataExtractionOutput Dataclass

```python
@dataclass
class ProfilingDataExtractionOutput:
    profile_id: str
    extraction_timestamp: str
    source_metadata: SourceMetadata
    message_extractions: List[MessageExtraction]  # Per-message results
    aggregated_profile: AggregatedProfile  # Combined profile data
    extraction_metadata: ExtractionMetadata
```

### Per-Message Extraction Results

Each message's extraction results are captured individually:

```python
@dataclass
class MessageExtraction:
    message_id: str
    timestamp: str
    sender_id: str
    dimension_outputs: {
        "core_identity": {
            "extracted": true,
            "data": {
                "profession": "Software Engineer",
                "employer": "Microsoft"
            },
            "confidence": 0.92
        },
        "opinions_views": {
            "extracted": false,
            "data": null,
            "reason": "No opinions expressed"
        },
        "preferences_patterns": {
            "extracted": true,
            "data": {
                "work_preference": "early_morning",
                "pattern_type": "productivity"
            },
            "confidence": 0.85
        },
        # ... other dimensions
    }
    extraction_status: "success"  # or "partial", "failed"
```

### Aggregated Profile Data

The combined results across all messages:

```python
aggregated_profile: {
    "extracted_data": {
        "core_identity": {
            "name": "Alex Chen",
            "age": 28,
            "profession": "Software Engineer",
            "employer": "Microsoft",
            "location": "Seattle, WA",
            "confidence": 0.95
        },
        "opinions_views": [
            {
                "topic": "remote_work",
                "stance": "strongly_supportive",
                "reasoning": "Values flexibility and work-life balance",
                "confidence": 0.88
            }
        ],
        "preferences_patterns": [
            {
                "category": "work_schedule",
                "pattern": "early_morning_productivity",
                "frequency": "daily",
                "confidence": 0.92
            }
        ],
        "desires_needs": [
            {
                "type": "professional",
                "description": "Career advancement to senior role",
                "urgency": "medium_term",
                "confidence": 0.85
            }
        ],
        "life_narrative": {
            "recent_transitions": [
                {
                    "event": "job_change",
                    "from": "Amazon",
                    "to": "Microsoft",
                    "date": "2024-01",
                    "motivation": "Better work-life balance"
                }
            ],
            "milestones": ["First FAANG role", "Cross-country relocation"]
        },
        "events": [
            {
                "type": "professional",
                "description": "Started new role at Microsoft",
                "date": "2024-01-02",
                "significance": "high"
            }
        ],
        "entities": {
            "people": [
                {
                    "name": "Sarah Martinez",
                    "relationship": "manager",
                    "context": "professional",
                    "sentiment": "positive"
                }
            ],
            "organizations": [
                {
                    "name": "Microsoft",
                    "relationship": "employer",
                    "start_date": "2024-01"
                }
            ],
            "locations": [
                {
                    "name": "Seattle",
                    "type": "city",
                    "relationship": "current_residence"
                }
            ]
        }
    }
}
```

### Extraction Metadata

Additional information about the extraction process:

```python
extraction_metadata: {
    "extraction_config": "config_v2.1",
    "llm_model": "gpt-4",
    "processing_time_ms": 3420,
   
    "dimensions_processed": ["core_identity", "opinions_views", "preferences_patterns", "desires_needs", "events", "entities"],
    "dimensions_skipped": ["life_narrative"],
    "messages_processed": 150,
    "messages_with_extractions": 87,
    "extraction_rate": 0.58
}
```

## Data Flow Summary

1. **Input Source**: Messages are typically pulled from a database where conversation histories are stored (Slack exports, chat logs, support tickets, etc.)

2. **ProfilingInput Construction**: The raw messages are wrapped into the `ProfilingInput` dataclass along with the appropriate configuration

3. **Pipeline Processing**: The Profile Miner runs its internal extraction pipeline:
   - Validates and preprocesses messages
   - Executes LLM-powered extraction for each configured dimension
   - Integrates results across dimensions
   - Resolves conflicts and scores confidence

4. **Structured Output**: The system returns a `ProfilingDataExtractionOutput` dataclass containing both per-message extractions and aggregated profile data, ready for:
   - Storage in profile databases
   - Feeding into recommendation engines
   - Analysis and visualization
   - Integration with downstream AI systems

## Key Design Principles

### Modularity
Each dimension is processed independently, allowing for:
- Parallel processing
- Dimension-specific optimization
- Easy addition of new dimensions

### Configurability
Every aspect of extraction can be configured:
- Which dimensions to extract
- Extraction granularity
- Confidence thresholds
- Output formats

### Scalability
The pipeline is designed to handle:
- Single conversations or bulk processing
- Real-time or batch extraction
- Various message volumes (10s to 100,000s of messages)

### Privacy-First
Built-in privacy controls:
- Configurable PII handling
- Audit modes for compliance
- Data minimization options
