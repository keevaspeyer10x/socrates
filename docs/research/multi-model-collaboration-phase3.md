# Multi-Model Collaborative Intelligence - Phase 3

**Session Date**: 2026-01-22
**Goal**: Broaden from problem-solving to COLLABORATIVE WORKFLOW EXECUTION
**Budget**: ~$100 | **Spent so far**: ~$1.30

---

## The Reframe: From Problem-Solving to Workflow Execution

### Phase 1-2 Focus (What We Had)
- Debate, dialectical synthesis, fork-merge, tribunal protocol
- Output: Decisions, architectures, plans (TEXT)
- Pattern: "Models collaborate to decide what to do"

### Phase 3 Focus (What We're Adding)
- Collaborative execution of workflows (coding, operations, pipelines)
- Output: State changes in the world (CODE, DEPLOYMENTS, DATA)
- Pattern: "Models collaborate to DO things together"

### The Key Distinction

| Collaborative Problem-Solving | Collaborative Workflow Execution |
|-------------------------------|----------------------------------|
| Output is decisions/text | Output is state changes |
| Success = consensus/quality | Success = working system |
| Verification is subjective | Verification is objective (tests pass) |
| Loose coupling between contributions | Tight dependencies (code must integrate) |
| Can iterate indefinitely | Bounded by real-world constraints |

---

## Dogfooding Lessons: What We're Learning FROM This Research Process

### The Process We're Running
We're using our own Fork-Merge pattern to conduct this research:
- 4 parallel research tracks (different domains)
- Each track queries multiple models independently
- Merge phase synthesizes across tracks

### Lessons Observed

| Observation | Lesson for Framework |
|-------------|---------------------|
| Parallel tracks produce genuinely different insights | **Forced heterogeneity works** - different prompts → different emphases |
| Background tasks enable parallelism but need monitoring | **Orchestration layer needed** for tracking state of parallel work |
| Each model naturally emphasizes different aspects | **Model diversity = perspective diversity** - exploit, don't suppress |
| The merge phase is where synthesis happens | **Merge is not aggregation** - requires active integration work |
| Some tracks take longer than others | **Async coordination** is essential - don't block on slowest |
| Results need structured extraction | **Shared artifact schema** helps merge - not free-form text |

### What's Working
1. **Explicit role prompts**: Asking each track to focus on specific domain
2. **Structured questions**: Same question structure across tracks enables comparison
3. **Background execution**: Parallelism dramatically speeds research
4. **Cost tracking**: Budget awareness keeps experiments bounded

### What's Hard
1. **Merging large outputs**: Token limits make synthesis challenging
2. **Tracking provenance**: Which insight came from which model/track?
3. **Detecting redundancy**: Similar insights expressed differently
4. **Knowing when to stop**: How many tracks are enough?

---

## Research Tracks (Fork-Merge Pattern - Dogfooding)

### Track 1: Human Workflow Collaboration Patterns
*Focus: What can we learn from pair programming, mob programming, OSS, surgical teams?*

**Key Questions:**
- What makes human workflow collaboration work?
- What are the failure modes?
- What would AI-native versions look like?

**Findings:**

| Human Pattern | Core Mechanism | AI-Native Translation |
|---------------|----------------|----------------------|
| **Pair Programming** | Driver/Navigator role split + micro-turn-taking | Asymmetric prompts: one generates, one critiques each output |
| **Mob Programming** | 3+ participants, rotating driver, consensus via discussion | Moderator + specialist ensemble with weighted voting |
| **OSS Collaboration** | Async PRs, CODEOWNERS, CI gates, module ownership | Agent "contributors" file diffs, reviewer agents gate merges |
| **Surgical Teams** | Checklists, CRM readbacks, shared situational awareness | Protocol-enforced queries ("Confirm step X?" - "Confirmed") |

**Key Insight**: Human workflow collaboration works via **artifact-mediated coordination** + **role specialization** + **gating mechanisms**. AI-native versions need explicit handoff contracts and machine-enforceable gates.

---

### Track 2: Adjacent Fields
*Focus: CSCW, distributed systems, formal methods, workflow systems, classic MAS*

**Key Questions:**
- What coordination mechanisms exist in other fields?
- What's directly applicable to multi-model AI?
- What failure modes should we avoid?

**Findings:**

| Field | Key Concept | Steal for AI Collaboration |
|-------|-------------|---------------------------|
| **CSCW** | Grounding loops, artifact-mediated collaboration | Iterative propose/acknowledge via shared state |
| **Distributed Systems** | CRDTs, eventual consistency, consensus protocols | Mergeable state for parallel work; Raft for critical decisions |
| **Formal Methods** | Contracts, types, pre/post-conditions | Agent APIs with machine-checkable invariants |
| **Workflow Systems** | Temporal/Airflow, durable execution, sagas | Compensatable tasks, checkpoint/resume on failure |
| **Classic MAS** | Blackboard, Contract Net Protocol, BDI | Bidding for tasks, explicit intention management |

**Synthesis**: A multi-model system should be:
- **Durably executed** (Temporal-style checkpointing)
- **Eventually consistent** (CRDT-based shared state)
- With **formal contracts** as coordination anchors
- Using **blackboard + bidding** for dynamic task allocation

---

### Track 3: Execution vs Problem-Solving Framework
*Focus: What fundamentally distinguishes collaborative ideation from collaborative execution?*

**Key Questions:**
- What does "collaboration during execution" mean?
- What makes it hard for AI specifically?
- What would "genuine collaborative execution" look like?

**Findings:**

**The Fundamental Distinction (consensus across all models):**

| Dimension | Collaborative Ideation | Collaborative Execution |
|-----------|------------------------|------------------------|
| **Output** | Decisions/text/plans | State changes (commits, deploys, data) |
| **State** | Volatile (context window) | Persistent (file system, database) |
| **Reversibility** | High (just say something different) | Low (rollbacks have real cost) |
| **Success metric** | Consensus/coherence | Working system (tests pass) |
| **Failure mode** | Disagreement | Crash/corruption |
| **Dynamic** | Dialectical (thesis→synthesis) | Transactional (lock→modify→commit) |

**The Framework (from Grok):**
> "Collaborative ideation coordinates **beliefs**; collaborative execution coordinates **interventions**."

**Execution Collaboration Topologies:**
1. **Relay** (sequential handoffs) - AI-suitable
2. **Swarm** (parallel + merge) - Medium difficulty
3. **Gatekeeper** (adversarial review) - AI-suitable
4. **Cockpit** (real-time symbiosis) - Very hard for AI

**Why AI Struggles with Execution:**
- **Hidden state problem**: Context window is keyhole into massive repo
- **No social locking protocol**: Models overwrite each other
- **Feedback lag**: Interpreting systemic feedback requires perfect mental model

---

### Track 4: Academic Papers
*Focus: ChatDev, MetaGPT, AlphaCodium, Reflexion, SWE-bench, APR*

**Key Questions:**
- What architectures have been tried?
- What coordination mechanisms work?
- What can we steal for our framework?

**Findings:**

| System | Key Mechanism | Steal for Framework |
|--------|---------------|---------------------|
| **ChatDev** | Role-based dyadic chat chains | Inception prompting for role reversal; mandatory critique steps |
| **MetaGPT** | SOPs + Pub/Sub architecture | Structured artifacts between agents; subscribe to document events |
| **AlphaCodium** | Test-first flow engineering | Generate tests before code; inner loop of generate→run→repair |
| **Reflexion** | Verbal reinforcement from traces | Prepend failure reflections to retry prompts |
| **SWE-bench** | Tool-use over text-gen | File/shell interface; exploration before editing |
| **APR/GenProg** | Generate-and-validate loops | Parallel candidates; test harness as central coordinator |

**Unified Recipe from Academic Work:**
1. **Structure** (MetaGPT): Pub/Sub with structured artifacts, not chat
2. **Process** (AlphaCodium): Test → Code → Validate loop
3. **Resilience** (Reflexion): Reflection step before retry
4. **Interface** (SWE-bench): Shell/file system tools for exploration

---

## Synthesis: Unified Framework for Collaborative Workflow Execution

### The Two Modes: Ideation vs Execution

Our research reveals multi-model collaboration has **two fundamentally different modes**:

```
┌─────────────────────────────────────────────────────────────────┐
│                  COLLABORATIVE IDEATION                          │
│  (What we solved in Phase 2)                                     │
│                                                                  │
│  Debate → Fork-Merge → Tribunal → Synthesis                     │
│  Output: Decisions, plans, architectures (TEXT)                 │
│  Coordination: Beliefs → Consensus                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
              [Commit Point: Spec → Tests → Contract]
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                  COLLABORATIVE EXECUTION                         │
│  (What we're solving in Phase 3)                                │
│                                                                  │
│  Spec → Test-Gen → Code → Validate → Merge                      │
│  Output: State changes (CODE, DATA, DEPLOYMENTS)                │
│  Coordination: Interventions → Working System                    │
└─────────────────────────────────────────────────────────────────┘
```

### The Unified Architecture

Combining insights from all 4 tracks:

```
┌───────────────────────────────────────────────────────────────────────┐
│                    COLLABORATIVE WORKFLOW ENGINE                       │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              BLACKBOARD (Shared Persistent State)               │   │
│  │  specs | tests | code | artifacts | disputes | reflections     │   │
│  │  [CRDT-based for parallel work, Raft for critical decisions]   │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                              ▲                                         │
│      ┌───────────────────────┼───────────────────────┐                │
│      │                       │                       │                │
│  ┌───┴───┐              ┌────┴────┐             ┌────┴───┐           │
│  │IDEATE │    commit    │ SPECIFY │   commit    │EXECUTE │           │
│  │       │   ────────►  │         │  ────────►  │        │           │
│  │Debate │    specs     │Test-Gen │   tests     │Code-Gen│           │
│  │Fork   │              │Contract │             │Validate│           │
│  │Merge  │              │Review   │             │Merge   │           │
│  └───────┘              └─────────┘             └────────┘           │
│      │                       │                       │                │
│  [Phase 2                [Bridge:               [Phase 3              │
│   Patterns]              Spec as                 Patterns]            │
│                          Contract]                                    │
│      │                       │                       │                │
│      └───────────────────────┴───────────────────────┘                │
│                              │                                         │
│                    [Failure? Reflect → Loop back]                     │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

### Key Components

**1. Blackboard (Shared State)**
- CRDT-based for parallel exploration
- Raft consensus for critical decisions
- Versioned, auditable, observable

**2. Role Specialization**
| Role | Responsibility | Constraints |
|------|----------------|-------------|
| Navigator | Strategic context, architecture | Read-only on code |
| Specifier | Requirements → tests | Cannot write implementation |
| Builder | Code generation | Cannot modify tests |
| Validator | Run tests, lint, verify | Cannot fix—only report |
| Reviewer | Critique, security, style | Cannot approve own work |
| Integrator | Merge, conflicts, release | Requires green CI |

**3. Coordination Protocols**
- **Pub/Sub** for artifact events (MetaGPT)
- **Contract Net** for task allocation (bidding)
- **Gating** at phase transitions (CI as judge)
- **Reflection loops** on failure (Reflexion)

**4. Execution Loop**
```
1. Spec → (Navigator + Specifier)
2. Test-Gen → (Specifier writes failing tests)
3. Code-Gen → (Builder implements)
4. Validate → (Validator runs suite)
5. IF FAIL: Reflect → Loop to step 3 (max 3)
6. IF PASS: Review → (Reviewer critiques)
7. IF APPROVED: Merge → (Integrator commits)
```

### The Four Evaluation Questions

When evaluating any multi-model collaboration system:

1. **Where is the shared truth stored?** (Authoritative state, not chat)
2. **What are the coordination protocols?** (Handoffs, locks, approvals)
3. **What are the invariants and who enforces them?** (Safety + quality gates)
4. **How tight is the reality-feedback loop?** (Tests/telemetry; can it halt action)

### What We Learned from Dogfooding

Running this research using Fork-Merge revealed:
- **Parallel tracks work**: 4 domains explored simultaneously
- **Merge is the hard part**: Synthesizing 71KB+ of outputs
- **Structure enables comparison**: Same questions across tracks
- **Async is essential**: Don't block on slowest track
- **Provenance matters**: Need to track which insight came from where

### Immediate Next Steps

1. **Prototype the Blackboard**: JSON state with CRDT operations
2. **Implement Role Constraints**: Permission-based agent prompts
3. **Build Test-First Loop**: Specifier→Builder pipeline
4. **Add Reflection Memory**: Failure analysis → retry enhancement
5. **Create Evaluation Rubric**: The 4 questions as scoring framework

---

## Cost Tracking (Phase 3)

| Experiment | Cost | Cumulative |
|------------|------|------------|
| Broadening query | $0.07 | $0.07 |
| Track 1: Human patterns | $0.07 | $0.14 |
| Track 2: Adjacent fields | $0.06 | $0.20 |
| Track 3: Execution framework | $0.08 | $0.28 |
| Track 4: Academic papers | $0.10 | $0.38 |
| **Total Phase 3** | **~$0.38** | |
| **Phase 1 + 2 + 3** | **~$1.54** | |

Budget remaining: ~$98.46

---

*Research conducted 2026-01-22. Dogfooding Fork-Merge pattern across 4 parallel tracks.*

