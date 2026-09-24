# ReAct Loop: Agent Reasoning Flow

**How AI Agents Plan, Act, and Observe**

---

## ReAct Loop Architecture

```mermaid
stateDiagram-v2
    [*] --> ReceiveQuery

    ReceiveQuery --> Plan: Generate thought
    Plan --> Decide: Choose action

    state Decide {
        [*] --> ToolUse: Need external info
        [*] --> Generate: Have enough info
    }

    ToolUse --> Execute: Call tool/function
    Execute --> Observe: Get result
    Observe --> Plan: Update thought

    Decide --> Generate: Formulate answer
    Generate --> [*]: Return response
```

---

## Detailed ReAct Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant A as Agent
    participant T as Tools
    participant L as LLM

    U->>A: Query
    A->>A: Thought 1: What do I need?
    A->>T: Action 1: Use tool
    T-->>A: Observation 1: Result

    A->>A: Thought 2: What now?
    A->>T: Action 2: Another tool
    T-->>A: Observation 2: Result

    A->>A: Thought 3: Have all info
    A->>L: Generate final answer
    L-->>A: Response
    A-->>U: Final Answer
```

---

## ReAct Prompt Structure

```mermaid
graph TD
    subgraph "ReAct Prompt Template"
        Q[Query: User Question]
        T[Thought: Reasoning]
        A[Action: Tool Call]
        O[Observation: Result]

        Q --> T
        T --> A
        A --> O
        O --> T

        T --> F{Final Answer?}
        F -->|No| A
        F -->|Yes| R[Response]
    end
```

---

## Tool Calling Flow

```mermaid
graph LR
    subgraph "Agent Processing"
        THOUGHT[Thought: Reasoning]
        DECIDE{Need Tool?}
    end

    subgraph "Tool Execution"
        PARSE[Parse Tool Name]
        PARAMS[Extract Parameters]
        EXEC[Execute Tool]
    end

    subgraph "Result Processing"
        OBSERVE[Observation: Result]
        UPDATE[Update Context]
    end

    THOUGHT --> DECIDE
    DECIDE -->|Yes| PARSE
    DECIDE -->|No| ANSWER[Generate Answer]

    PARSE --> PARAMS
    PARAMS --> EXEC
    EXEC --> OBSERVE
    OBSERVE --> UPDATE
    UPDATE --> THOUGHT
```

---

## Multi-Step Reasoning Example

```mermaid
stateDiagram-v2
    [*] --> Question: "What's the weather in Tokyo?"

    Question --> Thought1: "Need weather info"
    Thought1 --> Action1: "Call weather API"
    Action1 --> Obs1: "Got weather data"

    Obs1 --> Thought2: "Need location confirmation"
    Thought2 --> Action2: "Search Tokyo coordinates"
    Action2 --> Obs2: "Got coordinates"

    Obs2 --> Thought3: "Have all info"
    Thought3 --> Answer: "Tokyo is 18°C, sunny"

    Answer --> [*]
```

---

## ReAct vs Standard LLM

```mermaid
graph TB
    subgraph "Standard LLM"
        LQ[User Question]
        LA[LLM Processing]
        LR[Response]
        LQ --> LA
        LA --> LR
    end

    subgraph "ReAct Agent"
        AQ[User Question]
        AT[Thought 1]
        AA[Action 1]
        AO[Observation 1]
        AT2[Thought 2]
        AA2[Action 2]
        AO2[Observation 2]
        AR[Final Response]

        AQ --> AT
        AT --> AA
        AA --> AO
        AO --> AT2
        AT2 --> AA2
        AA2 --> AO2
        AO2 --> AR
    end
```

---

## Tool Types in ReAct

```mermaid
graph LR
    subgraph "Available Tools"
        SEARCH[Search Engine<br/>Web info]
        CALC[Calculator<br/>Math]
        CODE[Code Executor<br/>Run code]
        DB[Database Query<br/>Structured data]
        API[API Caller<br/>External services]
    end

    subgraph "Agent Decision"
        QUERY[Query Analysis]
        SELECT[Tool Selection]
    end

    QUERY --> SELECT
    SELECT --> SEARCH
    SELECT --> CALC
    SELECT --> CODE
    SELECT --> DB
    SELECT --> API
```

---

## Error Handling in ReAct

```mermaid
stateDiagram-v2
    [*] --> Execute
    Execute --> Success{Tool Success?}

    Success -->|Yes| Observe
    Success -->|No| Recover

    Recover --> Thought{Can Recover?}
    Thought -->|Yes| Alternative[Try alternative tool]
    Thought -->|No| Error[Return error]

    Alternative --> Execute
    Observe --> Next{More Info?}

    Next -->|Yes| Plan
    Next -->|No| Final[Generate answer]

    Final --> [*]
    Error --> [*]
```

---

**Last Updated:** 2026-02-04
**Related:** [7101-ReAct-Loop-System.md](../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)
