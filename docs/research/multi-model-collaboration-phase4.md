# Multi-Model Collaborative Intelligence - Phase 4

**Session Date**: 2026-01-22
**Goal**: Deep iteration - go wider, deeper, novel directions with 3 full iterations
**Budget**: ~$100 | **Spent so far**: ~$1.54

---

## The Expanded Scope

### From Orchestrator to General Framework

The existing orchestrator has 5 phases: **PLAN → EXECUTE → REVIEW → VERIFY → LEARN**

We're generalizing this to understand:
1. What SKILLS are needed at each stage (not just roles)
2. How QUALITY is ensured collaboratively
3. How LEARNING feeds back into future work
4. What FAILURE MODES exist and how to recover
5. What NOVEL PATTERNS we might be missing

### Research Method: 3 Full Iterations

**Iteration 1**: Broad exploration (6 parallel experiments)
**Iteration 2**: Deep dive on promising patterns
**Iteration 3**: Novel synthesis and integration

---

## Iteration 1: Broad Exploration

### Experiments Running

| # | Topic | Focus |
|---|-------|-------|
| 1 | Novel patterns | Beyond debate - biological, social, physical systems |
| 2 | QA collaboration | How models ensure quality together |
| 3 | Learning patterns | How models learn from each other |
| 4 | General workflow stages | Universal stages across domains |
| 5 | Skills vs roles | Dynamic capability routing |
| 6 | Failure modes | Resilience and recovery |

### Experiment 1: Novel Collaboration Patterns
*Focus: Biological, social, physical, gaming, creative systems*

**Key Patterns Discovered:**

| Pattern | Inspiration | AI Application |
|---------|-------------|----------------|
| **Stigmergic Sculpting** | Ant colonies, termite mounds | Agents modify shared artifacts; changes themselves are coordination signals |
| **Immunological Consensus** | Immune system (T-cells, antibodies) | Multiple validation "antibodies" attack solutions; survivors pass |
| **Prediction Market Synthesis** | Stock markets, betting markets | Models bid on solution quality; market price = confidence signal |
| **Swarm Gradient Climbing** | Bird flocking, fish schooling | Models follow "quality gradients" toward better solutions |
| **Jazz Improvisation Ensemble** | Musical improvisation | Models respond to each other's outputs in real-time, building on riffs |

**Key Insight:** These patterns share a common theme: **indirect coordination through shared artifacts or signals** rather than explicit negotiation.

---

### Experiment 2: Quality Assurance Collaboration
*Focus: Testing, review, validation, adversarial quality*

**QA Collaboration Modes:**

| Mode | Mechanism | AI Translation |
|------|-----------|----------------|
| **Testing Collaboration** | Dedicated test-writers vs implementers | "Coder cannot modify tests; Tester cannot write implementation" |
| **Review Collaboration** | PR/code review workflows | Reviewer agents score on criteria; cannot approve own work |
| **Validation Hierarchies** | CI/CD pipelines as judges | Tests/linters/type-checkers as "objective judges" |
| **Adversarial Quality (Red/Blue)** | Security red teams | Attack model tries to break; Defense model patches |
| **Consensus on Quality** | Multiple reviewers vote | N reviewers must agree before merge |

**Key Insight:** Quality collaboration requires **separation of concerns** (proposal vs critique) and **external grounding** (tests, compilers) as the source of truth.

---

### Experiment 3: Learning and Continuous Improvement
*Focus: Retrospectives, knowledge capture, continuous improvement*

**The LEARN Framework:**

```
L - Log: Capture all decisions, outcomes, failures
E - Exchange: Share lessons across agents
A - Articulate: Convert tacit patterns to explicit rules
R - Review: Periodic retrospectives on what worked
N - Next: Apply lessons to upcoming work
```

**Learning Mechanisms:**

| Mechanism | Description | Implementation |
|-----------|-------------|----------------|
| **Reflexion Memory** | Store verbal summaries of failures | Prepend to retry prompts |
| **Transactive Memory** | "Who knows what" catalog | Route queries to expert agents |
| **Collaborative Retrospectives** | Multi-model post-mortems | Structured "what worked/didn't" |
| **Pattern Mining** | Extract recurring solutions | Build reusable templates |

**Key Insight:** LLMs "learn" via **context updates**, not weight updates. Storing distilled lessons (not raw transcripts) in retrievable memory creates "verbal reinforcement learning."

---

### Experiment 4: General Workflow Stages
*Focus: Universal stages across all domains*

**Universal CYCLE Framework:**

```
C - Conceive   (Define problem, requirements, goals)
Y - Yield Plan (Design approach, decompose work)
C - Create     (Execute, build, implement)
L - Look Back  (Review, verify, test)
E - Evolve     (Learn, improve, iterate)
```

**Mapping to Orchestrator:**

| CYCLE Stage | Orchestrator Phase | Key Skills |
|-------------|-------------------|------------|
| Conceive | PLAN | Analysis, decomposition, creativity |
| Yield Plan | PLAN | Architecture, estimation, risk assessment |
| Create | EXECUTE | Implementation, integration, tool use |
| Look Back | REVIEW + VERIFY | Critique, testing, validation |
| Evolve | LEARN | Reflection, pattern extraction, adaptation |

**Key Insight:** All workflows across domains share these stages, but the **skills needed at each stage vary by domain and task complexity**.

---

### Experiment 5: Skills vs Roles
*Focus: Dynamic capability routing, transactive memory*

**Skills Taxonomy:**

| Category | Skills | When Needed |
|----------|--------|-------------|
| **Technical** | Coding, testing, debugging, architecture | EXECUTE phase |
| **Meta** | Planning, estimation, risk assessment | PLAN phase |
| **Social** | Negotiation, consensus-building, teaching | REVIEW phase |
| **Quality** | Critique, verification, security review | VERIFY phase |
| **Learning** | Pattern recognition, knowledge capture | LEARN phase |

**DYNAMIC-CAP Protocol:**

```
D - Detect task requirements
Y - Yield skill requirements from task
N - Navigate to capable agents
A - Assign based on availability + capability
M - Monitor execution quality
I - Iterate if skill mismatch detected
C - Capture skill performance data
```

**Key Insight:** **Skills are more granular than roles**. A "Reviewer" role needs critique skills + domain knowledge + security awareness. Dynamic skill routing enables better matching than static role assignment.

---

### Experiment 6: Failure Modes and Recovery
*Focus: Resilience framework for multi-model systems*

**Failure Taxonomy:**

| Category | Failure Modes | Recovery Strategy |
|----------|---------------|-------------------|
| **Coordination** | Deadlock, race conditions, lost updates | Timeouts, locks, conflict resolution |
| **Communication** | Misunderstanding, context loss, drift | Structured protocols, checkpoints |
| **Quality** | Bugs, regressions, security issues | Gates, rollback, automated testing |
| **Resource** | Token limits, timeout, cost overrun | Budgets, chunking, early termination |
| **Goal** | Scope creep, wrong direction, misalignment | Regular alignment checks, invariants |

**RESILIENT Framework:**

```
R - Redundancy: Multiple agents for critical tasks
E - Encapsulation: Isolate failures to components
S - Sensing: Detect problems early (monitoring)
I - Isolation: Prevent failure propagation
L - Limiting: Bound blast radius (timeouts, budgets)
I - Iteration: Small steps with frequent checkpoints
E - Escalation: Clear paths to human intervention
N - Normalization: Graceful degradation when needed
T - Tolerance: Design for partial failures
```

**Key Insight:** Multi-model systems fail in characteristic ways that single-model systems don't: **coordination failures, context loss, and cascading errors**. Building resilience requires explicit mechanisms at each layer.

---

## Iteration 1 Synthesis

### Cross-Cutting Themes

1. **Artifact-Centered Coordination** beats conversation-centered coordination
   - Shared artifacts (code, tests, specs) provide ground truth
   - Changes to artifacts ARE coordination signals (stigmergic)
   - External validators (tests, compilers) provide objective feedback

2. **Separation of Concerns** is essential for quality
   - Proposers vs Critics (cannot approve own work)
   - Test writers vs Implementers (prevent moving goalposts)
   - Planners vs Executors vs Verifiers (clear responsibilities)

3. **Skills > Roles** for dynamic collaboration
   - Roles are bundles of skills
   - Dynamic skill routing enables better matching
   - Transactive memory tracks "who knows what"

4. **Learning requires explicit mechanisms**
   - Verbal reinforcement via reflection memory
   - Distilled lessons, not raw transcripts
   - Pattern extraction and template building

5. **Resilience must be designed in**
   - Expect coordination failures
   - Build rollback/checkpoint mechanisms
   - Design for partial failures

### The Unified Model (Draft)

```
┌─────────────────────────────────────────────────────────────────────────┐
│            MULTI-MODEL COLLABORATIVE WORKFLOW ENGINE                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    BLACKBOARD (Shared State)                     │    │
│  │  Artifacts: specs | tests | code | reviews | lessons | disputes │    │
│  │  Protocol: CRDT for parallel work, Raft for critical decisions  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              ▲                                           │
│      ┌───────────────────────┼───────────────────────┐                  │
│      │                       │                       │                  │
│  ┌───┴───┐              ┌────┴────┐             ┌────┴───┐              │
│  │CONCEIVE│   commit    │ CREATE  │   commit    │  LOOK  │              │
│  │+PLAN  │  ────────►   │         │  ────────►  │  BACK  │              │
│  │       │    spec      │Build+   │   code      │Review+ │              │
│  │Debate │              │Execute  │             │Verify  │              │
│  └───────┘              └─────────┘             └────────┘              │
│      │                       │                       │                  │
│      │                       │                       │                  │
│      └───────────────────────┴───────────────────────┘                  │
│                              │                                           │
│                        ┌─────┴─────┐                                    │
│                        │  EVOLVE   │                                    │
│                        │ (LEARN)   │                                    │
│                        │Reflexion  │                                    │
│                        │Patterns   │                                    │
│                        └───────────┘                                    │
│                                                                          │
│  [SKILL ROUTER]  ←──→  [RESILIENCE LAYER]  ←──→  [MEMORY SYSTEMS]       │
│   - DYNAMIC-CAP         - RESILIENT              - Reflexion            │
│   - Transactive         - Checkpoints            - Transactive          │
│   - Capability map      - Rollback               - Pattern library      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Promising Patterns for Iteration 2 Deep Dive

1. **Stigmergic Artifact Coordination** - Indirect coordination through shared artifacts
2. **DYNAMIC-CAP Skill Routing** - Dynamic capability assignment protocol
3. **RESILIENT Recovery Framework** - Comprehensive failure handling
4. **LEARN Cycle Integration** - Systematic learning feedback loop
5. **Test-First Adversarial Loop** - TDD with separated test/impl roles

---

## Iteration 2: Deep Dive

Based on Iteration 1 findings, we're going deeper on the 5 most promising patterns:

### Deep Dive 1: Stigmergic Artifact Coordination
*Focus: How exactly does indirect coordination through shared artifacts work?*

**Core Mechanism (Consensus):**
- **Blackboard/event-sourced shared artifact system** where agents coordinate by reading/writing structured state + metadata "signals"
- Selective sensing via events/filters/embeddings
- Concurrency via versioning/leases/propose→merge

**The "Pheromone" Equivalent:**
| Signal Type | Examples | Purpose |
|-------------|----------|---------|
| **Explicit Tags** | `@status: draft/frozen`, `@confidence: 0.4`, `@error: SyntaxError` | Direct coordination cues |
| **Provenance** | Agent ID, timestamp, version | Track changes and ownership |
| **Negative Signals** | Cooldowns, "do-not-edit-until", "known-bad" markers | Prevent failure loops |
| **Implicit Signals** | Entropy hotspots, semantic drift from goal embedding | Emergent coordination |

**Agent Behavior Protocol:**
```
1. Subscribe to relevant signal types (events/tags)
2. Query artifact with vector search for semantically relevant chunks
3. On match: evaluate condition → take action → emit new signals
4. Repeat
```

**Concurrency Control:**
- **Optimistic versioning** with `base_version` checks and retry/rebase
- **Leases/soft locks** at task or region granularity
- **Proposals/patches** written append-only; **merger/arbiter agent** applies them
- CRDTs optional for fine-grained concurrent edits

**Failure Detection & Recovery:**
- Detect: high churn/oscillation, low progress, duplicate proposals, contradictions
- Recover: cooldowns/decay, freeze + escalate to review, re-plan pulses, branch and choose winner

**Best-Fit Tasks:** Code+tests, research→claims, long-form docs, checklist/compliance, data pipelines

---

### Deep Dive 2: DYNAMIC-CAP Skill Routing
*Focus: Implementation details for skill-based agent routing*

**Skill Representation (Hybrid Model):**
```python
class AgentSkillProfile:
    agent_id: str
    # Ontology: Hard capabilities
    tools: List[str]           # ["google_search", "pandas", "jira_api"]
    constraints: List[str]     # ["requires_internet", "read_only_db"]

    # Semantic: Soft skills
    description: str           # "Specializes in async Python refactoring"
    embedding: Vector[768]     # Generated from description + history

    # Performance (Beta distribution for uncertainty)
    skill_beliefs: Dict[str, BetaDistribution]  # skill_id → (α, β)
```

**Task Analysis Protocol:**
1. LLM-based extraction → structured JSON (required skills, weights, min proficiency, constraints)
2. Normalize extracted skills to canonical IDs via aliases + embedding nearest-neighbor
3. Output task DAG for multi-skill work

**Routing Algorithm:**
```
1. FILTER: Hard constraints gating (tools, permissions) → eligible agents only
2. RETRIEVE: Top-K semantic candidate retrieval via embedding similarity
3. SCORE: Composite match score = skill_fit × uncertainty_penalty × recency × load_factor
4. ASSIGN: Select best agent (or team for multi-skill tasks)
5. MONITOR: Track execution quality, intervention policies
6. UPDATE: Feed outcomes back as evidence → update Beta beliefs
```

**Team Formation for Multi-Skill Tasks:**
- Prefer **decompose → route subtasks → integrate**
- For non-decomposable: **greedy set-cover heuristic** over required skills

**Exploration Policy:**
- UCB/LCB routing based on task risk tolerance
- Epsilon-greedy style exploration for capability discovery

---

### Deep Dive 3: RESILIENT Recovery Framework
*Focus: Concrete implementation for multi-model failure recovery*

**Sensing Layer:**

| Signal | Detection Method |
|--------|------------------|
| Stalls/Deadlock | Heartbeats, leases, watchdogs |
| Loops | Similarity hash over last N messages (>0.95 = loop) |
| Context Drift | Semantic anchoring (cosine similarity to goal embedding) |
| State Corruption | Hash/version mismatch, missing artifact references |

**Failure Classification:**
- **TRANSIENT**: Network, rate limits → retry with backoff
- **LOGIC**: Bug in reasoning → enhance context, switch approach
- **STATE_CORRUPTION**: Invalid state → rollback to checkpoint
- **SAFETY**: Policy violation → halt and escalate
- **UNKNOWN**: → conservative handling, human escalation

**Transaction/Checkpoint Model:**
```
BEGIN → EXECUTE → VALIDATE → COMMIT
         ↓           ↓
      Checkpoint  Rollback if invalid
```

**Checkpoint Boundaries (aligned with workflow):**
- Post-PLAN (approved spec)
- After each validated subtask commit
- Post-REVIEW approval
- Post-VERIFY pass
- Before irreversible side effects

**Recovery State Machine:**
```
DETECT → CLASSIFY → {
  TRANSIENT → RETRY (with backoff, jitter)
  LOGIC → ROLLBACK → REPLAN (with enhanced context)
  STATE → ROLLBACK → RESUME from checkpoint
  SAFETY → HALT → ESCALATE
  UNKNOWN → ESCALATE
}
```

**Preventing Retry Storms:**
- Exponential backoff + jitter
- Global circuit breakers per tool/service
- Rate limits and token budgets
- Idempotency/locks per task

**Human Escalation Protocol:**
- Provide "incident card": goal, failure, evidence, attempted fixes, options
- Resume via state injection recorded as event/new checkpoint
- Restart from failed step/milestone

---

### Deep Dive 4: LEARN Cycle Integration
*Focus: Systematic learning feedback implementation*

**Logging Schema (The 4-Tuple):**
```json
{
  "trace_id": "uuid",
  "agent_id": "agent_analyst_01",
  "task_id": "task_99",
  "timestamp": "ISO8601",
  "context": {
    "input": "...",
    "available_tools": [...],
    "relevant_history": "..."
  },
  "rationale": "The user wants X, I should use tool Y because...",
  "action": {
    "tool_name": "rag_search",
    "tool_args": {"query": "..."}
  },
  "outcome": {
    "status": "success|failure",
    "output": "...",
    "latency_ms": 450,
    "error_type": null
  }
}
```

**Tiered Storage Strategy:**
| Tier | Content | Retention |
|------|---------|-----------|
| Hot | Recent + high-value traces | Full fidelity |
| Warm | Older traces | Summaries + embeddings |
| Cold | Archive | Blob storage, artifacts by reference |

**Always log failures, sample successes (10-20%)**

**Articulation Pipeline (Meta-Agent):**
```
1. BATCH: Collect interesting traces (failures, high complexity, latency spikes)
2. CLUSTER: Group by tool/error/embedding similarity
3. DRAFT: Meta-agent generates IF-THEN rules / anti-patterns
4. VALIDATE: Dedupe, consistency checks, backtest/synthetic tests
5. PROMOTE: Store as lesson card in retrieval layer
```

**Lesson Card Schema:**
```json
{
  "lesson_id": "uuid",
  "trigger_context_embedding": [...],
  "guideline": "When encountering X, prefer approach Y because Z",
  "confidence": 0.85,
  "utility_score": 0.7,
  "version": 3,
  "created_at": "...",
  "last_applied": "...",
  "apply_count": 42
}
```

**Knowledge Exchange Protocol:**
1. At task start, retrieve top-K relevant lessons (threshold > 0.7)
2. Inject in dedicated prompt section: `<lessons>...</lessons>`
3. Cap at ~10% of context budget
4. Log "lesson applied" markers for feedback

**Retrospective Triggers:**
- Failure rate spike
- Workflow completion (milestone)
- Periodic (nightly/weekly)

**Retrospective Structure:**
1. Parallel critiques from multiple agents
2. Meta-agent adjudicates/synthesizes
3. Outputs: new lesson, revised prompt/tool spec, archived rule

**Reflexion vs LEARN:**
| Aspect | Reflexion | LEARN |
|--------|-----------|-------|
| Scope | Within-episode retry | Cross-episode persistent |
| Timescale | Immediate | Accumulated over time |
| Storage | Context window | Persistent retrieval layer |
| Bridge | Successful Reflexion corrections → high-signal LEARN inputs |

---

### Deep Dive 5: Test-First Adversarial Loop
*Focus: TDD with separated test/impl roles for multi-model coding*

**Role Separation Enforcement:**

| Role | Can Write | Cannot Write | Tools |
|------|-----------|--------------|-------|
| Tester | `/tests/`, `/spec/` | `/src/` | Test runner, spec validator |
| Implementer | `/src/` | `/tests/` | Compiler, linter, debugger |

**Technical Enforcement:**
- Path-based PR/CI gates
- CODEOWNERS requiring cross-role approval
- Orchestrator strips forbidden constructs from outputs

**Communication Protocol:**
- **Intent clarification**: Tester documents intent in spec; Implementer reads spec
- **Dispute resolution**: Formal `DisputeObject` → Spec Owner arbitrates
```json
{
  "type": "DISPUTE",
  "test_case": "test_refill_logic",
  "reason": "Test assumes instant refill; spec implies continuous",
  "suggested_fix": "Use time delta tolerance"
}
```

**Red-Green-Refactor State Machine:**

**RED (Tester's Turn):**
1. Write test tied to spec ID (e.g., `test_REQ_123_...`)
2. Run against stub/base → must fail with AssertionError
3. "Red on base" validation prevents false reds

**GREEN (Implementer's Turn):**
1. Write minimal `/src` changes to pass
2. No test modifications allowed
3. CI runs full suite including hidden tests

**REFACTOR (Implementer's Turn - Protected):**
1. Improve code structure
2. Suite must remain green
3. Tests generally locked (rare test-hygiene exceptions via Tester PR)

**Anti-Overfitting Measures:**
| Technique | Purpose |
|-----------|---------|
| Hidden/sealed tests | Implementer can't tailor to visible cases |
| Mutation testing | Surviving mutants fail build → force stronger tests |
| Property-based tests | Fuzzy coverage of edge cases |
| Boundary tests | Target limits, zeros, negatives |
| Table-driven tests | Force logic, prevent hardcoding |

**Spec-Test-Code Traceability:**
- Tag requirements in `/spec/` with stable IDs
- Test names include `REQ_ID`: `test_REQ_123_rate_limit_refill`
- Implementation tags: `@implements REQ-123`
- Auto-generate traceability matrix; lint for orphans

**Convergence Failure Recovery:**
1. Iteration cap (e.g., 3 cycles per requirement)
2. Timebox (e.g., 30 minutes)
3. Escalation ladder: simplify test → split requirement → architect review → spec revision
4. Circuit breaker: after N failed cycles, halt and escalate

---

### Iteration 2 Synthesis

**Key Findings Across Deep Dives:**

1. **Coordination is best done through artifacts, not conversation**
   - Stigmergic patterns (indirect coordination) are more scalable than explicit negotiation
   - Event-sourced state provides audit trail and rollback capability
   - Metadata "signals" (tags, confidence, provenance) enable selective attention

2. **Skills enable better matching than static roles**
   - Beta distribution beliefs model uncertainty about capabilities
   - Evidence-based updates from task outcomes improve routing over time
   - Decomposition + recursive routing handles multi-skill tasks

3. **Failure is expected and must be engineered for**
   - Typed failure classification enables targeted recovery strategies
   - Checkpoints at phase boundaries provide natural rollback points
   - Human escalation must be structured and resumable

4. **Learning requires explicit infrastructure**
   - Structured traces (not raw logs) enable pattern extraction
   - Lesson cards with retrieval enable cross-task learning
   - Reflexion (immediate) feeds into LEARN (persistent)

5. **Separation of concerns enables adversarial quality**
   - Enforced via tooling/permissions, not "politeness"
   - Tester and Implementer cannot modify each other's artifacts
   - External validation (tests, compilers) provides ground truth

---

## Iteration 3: Novel Synthesis

### Research Focus

Based on Iteration 1-2 findings, we're exploring:
1. **AI-Native Patterns**: Collaboration patterns with no human analog
2. **Generalized Framework**: Applying beyond software development
3. **Implementation Roadmap**: Practical path from research to production

### Experiment 1: AI-Native Novel Patterns
*Focus: What can AI do that humans fundamentally cannot?*

**Key Insight:** AI-native collaboration is "evolutionary computation on shared artifacts"—forking, mutating, testing, pruning, and distilling.

**AI-Native Capabilities:**
| Capability | Human Limitation | AI Pattern |
|------------|------------------|------------|
| Instant cloning | Can't duplicate self | Fork-merge parallelism |
| Perfect memory erasure | Can't selectively forget | "Lobotomy" for fresh perspectives |
| Direct state access | Must communicate via language | Embedding injection (synthetic telepathy) |
| Cheap disposability | Ego, attachment | Kill unsuccessful branches |
| Infinite patience | Fatigue, boredom | Massive redundancy as strategy |

**Novel Pattern Combinations:**

1. **Stigmergic + Adversarial = "Vandalism Protocol"**
   - Vandal agents randomly corrupt artifacts
   - Repair agents must fix damage
   - Artifact evolves antifragility through constant assault

2. **LEARN + Skill Routing = "Darwinian Skill Injection"**
   - Extract successful techniques from traces
   - Synthesize as skill LoRAs or prompt blocks
   - Inject into agent pool and A/B test
   - Agents evolve in real-time

3. **RESILIENT + Stigmergic = "Graveyard Map"**
   - Failed attempts leave "hazard markers"
   - Future agents navigate around known failures
   - Failures become coordination signals

**Counter-Intuitive Approaches:**
- **Hallucination Mining**: High-temperature "dreamer" agents generate wild ideas → grounding agent extracts viable logic
- **Massive Redundancy**: Token waste buys cognitive exploration
- **Chaos → Order Annealing**: Start chaotic (high temp), gradually converge

**The 10x Opportunity (Consensus):**
A self-evolving collaboration OS where:
1. Work forks into many executable timelines
2. Agents mutate + adversarially attack shared artifacts
3. Tests/typed failures leave persistent stigmergic signals
4. Distiller collapses branches into invariants + next tests
5. System updates routing + memory based on what survives

---

### Experiment 2: Generalized Framework
*Focus: Applying the framework across domains (creative, research, operations, strategy)*

**Universal Phase Model:**
```
INTENT → STRUCTURE → EXECUTION → CRITIQUE → AUDIT → SYNTHESIS
```

| Universal Phase | Software | Creative | Research | Operations | Strategy |
|----------------|----------|----------|----------|------------|----------|
| **INTENT** | Requirements | Theme/Goal | Research Question | Alert/Trigger | Problem Sensing |
| **STRUCTURE** | Architecture | Outline/Beat Sheet | Methodology Design | Incident Roles | Scenario Planning |
| **EXECUTION** | Coding | Drafting | Data Collection | Mitigation | Strategy Memo |
| **CRITIQUE** | Code Review | Developmental Edit | Peer Review | N/A | Red Teaming |
| **AUDIT** | Testing/CI | Fact-check/Canon | Statistical Validation | Health Metrics | Financial Modeling |
| **SYNTHESIS** | Deploy/Learn | Publish/Update Bible | Meta-analysis | Post-mortem | Decision/Monitor |

**Universal Roles:**
| Role | Function | Constraint |
|------|----------|------------|
| Visionary/Navigator | Sets direction | Cannot execute |
| Architect/Specifier | Defines constraints | Cannot build |
| Maker/Builder | Generates artifact | Cannot validate own work |
| Critic/Reviewer | Judges subjective quality | Cannot audit |
| Auditor/Validator | Checks objective truth | Cannot fix |
| Librarian/Integrator | Manages memory + merge | Requires gates passed |

**Domain-Specific Verification:**
| Domain | "Testing" Equivalent |
|--------|---------------------|
| Code | Unit tests, integration tests, CI |
| Creative | Continuity checks, fact-check, audience scoring, brand alignment |
| Research | Statistical validation, reproducibility, peer review |
| Operations | Health checks, SLOs, canaries, rollback readiness |
| Strategy | Simulations, premortems, pilots, leading indicators |

**Minimal Viable Framework:**
1. **Shared State**: Canonical artifact + backlog + assumption log + evidence + questions
2. **Loop**: Intent → Plan → Create → Critique → Validate → Learn
3. **Roles**: Navigator, Specifier, Builder, Reviewer, Validator, Integrator
4. **Gates**: Alignment to intent, coherence, domain verification, release readiness, learning capture

---

### Experiment 3: Implementation Roadmap
*Focus: Practical path from research to production*

**Phase 1: MVP ("Walking Skeleton")**
- **Goal**: Prove two agents can coordinate via shared state
- **Scope**: Single scenario (e.g., Writer-Reviewer loop)
- **Stack**:
  - Python + simple `while` loop orchestrator
  - Local `state.json` file
  - 2-3 hardcoded roles
  - Single LLM provider
- **Defer**: Dynamic routing, vector memory, databases, complex patterns
- **Safety**: Turn caps, token budgets, explicit stop criteria

**Phase 2: Foundation (Robustness + Observability)**
- **Storage**: Migrate to SQLite (WAL mode) for ACID
- **Schema**: `workflows` table (current state) + `events` table (append-only history)
- **Observability**: Structured logging, token/cost/latency metrics, correlation by `run_id`
- **Instrumentation**: Save critique→fix pairs for future learning
- **Tools**: Add sandboxing for code execution

**Phase 3: Sophistication (Add When Data Shows Need)**
- **Dynamic Routing**: When you have run history and cost/quality tradeoffs matter
  - Beta(α,β) per (agent, task_type)
  - Thompson sampling for exploration
- **Resilience**: When runs become long or tool failures are common
  - Event-sourced replay from checkpoints
  - Retry with enhanced context
- **Learning/RAG**: When tasks repeat and you can measure lift
  - Vector DB (ChromaDB/FAISS/pgvector)
  - "Lessons stored first" → then retrieval

**Technical Decisions:**
| Component | MVP | Foundation | Production |
|-----------|-----|------------|------------|
| State Storage | JSON file | SQLite | Postgres |
| Event Log | JSONL file | SQLite table | Postgres + Redis cache |
| Vector DB | None | None | Chroma/pgvector (when needed) |
| Orchestration | Custom loop | Custom FSM | LangGraph or Temporal |

**Risk Controls (From Day 1):**
- Max iterations per loop (e.g., 5)
- Token budget per run (e.g., 100K)
- Dollar budget per run (e.g., $1)
- Kill switch / human escalation triggers
- Sandboxed tool execution

**Evaluation Metrics:**
| Metric | Description |
|--------|-------------|
| Success rate | % runs passing acceptance criteria |
| Pass@1 | % passing on first attempt |
| Cost per success | Total $ / successful runs |
| Latency | Time to completion |
| Self-correction rate | % of critique→fix cycles |

**Baselines to Beat:**
1. Single-shot (one prompt, no iteration)
2. Single-model self-critique loop (better baseline)

---

### Iteration 3 Synthesis

**The Big Picture:**

Multi-model AI collaboration isn't about replicating human teamwork—it's about creating something fundamentally new: **evolutionary computation on shared artifacts**.

**Three Key Insights:**

1. **Artifact-First, Not Conversation-First**
   - Coordination happens through shared state, not chat
   - Changes to artifacts ARE the coordination signals
   - External validators (tests, compilers, metrics) provide ground truth

2. **Skills > Roles > Fixed Assignments**
   - Static role assignment limits adaptation
   - Skill-based routing with uncertainty tracking enables learning
   - Capability is empirical (demonstrated), not claimed

3. **Embrace Failure as Exploration**
   - Failures are first-class coordination signals
   - Typed failures enable targeted recovery
   - "Graveyard maps" prevent repeated mistakes

**The Unified Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MULTI-MODEL COLLABORATIVE WORKFLOW ENGINE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    BLACKBOARD (Event-Sourced State)                    │  │
│  │  Artifacts | Metadata Signals | Failure Markers | Lessons | Disputes  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    ▲                                         │
│      ┌─────────────────────────────┼─────────────────────────────┐          │
│      │                             │                             │          │
│  ┌───┴────┐        commit      ┌───┴───┐       commit       ┌────┴────┐    │
│  │ INTENT │  ─────────────►    │CREATE │  ─────────────►    │CRITIQUE │    │
│  │+STRUCT │      spec          │       │      artifact      │+AUDIT   │    │
│  │        │                    │Build  │                    │Review   │    │
│  │Navigate│                    │Execute│                    │Validate │    │
│  └────────┘                    └───────┘                    └─────────┘    │
│      │                             │                             │          │
│      │                             │                             │          │
│      └─────────────────────────────┴─────────────────────────────┘          │
│                                    │                                         │
│                              ┌─────┴─────┐                                  │
│                              │ SYNTHESIS │                                  │
│                              │  (LEARN)  │                                  │
│                              │ Distill   │                                  │
│                              │ Update    │                                  │
│                              └───────────┘                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  DYNAMIC-CAP       RESILIENT           STIGMERGIC        LEARN          ││
│  │  Skill Router      Recovery FSM        Signals           Lesson Store   ││
│  │  Beta beliefs      Checkpoints         Metadata          Retrieval      ││
│  │  Team formation    Escalation          Pheromones        Reflexion      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Mapping to Existing Orchestrator:**

| Orchestrator Phase | Framework Phase | Key Patterns |
|--------------------|-----------------|--------------|
| PLAN | INTENT + STRUCTURE | Fork-Merge ideation, skill routing |
| EXECUTE | CREATE | Test-first adversarial loop, stigmergic coordination |
| REVIEW | CRITIQUE | Separated reviewer role, cannot approve own work |
| VERIFY | AUDIT | External validation (tests, CI), quality gates |
| LEARN | SYNTHESIS | Lesson extraction, retrospectives, memory update |

---

## Dogfooding Lessons

### What We Learned From This Research Process

| Iteration | Observation | Framework Implication |
|-----------|-------------|----------------------|
| 1 | Parallel experiments produce diverse insights | **Fork-Merge works**: Different prompts → different emphases |
| 1 | Some experiments complete faster than others | **Async coordination essential**: Don't block on slowest |
| 1 | Synthesizing large outputs is challenging | **Merge is the hard part**: Need structured extraction |
| 2 | Deep dives revealed implementation details | **Depth requires iteration**: Surface patterns → concrete mechanisms |
| 2 | Models agreed on core patterns, disagreed on details | **Consensus ≠ unanimity**: Track disagreements as design forks |
| 3 | Novel patterns emerged from combining findings | **Synthesis creates novelty**: Fork → Merge → Novel combinations |
| 3 | Implementation roadmap grounded research | **Practical constraints clarify**: MVP thinking sharpens priorities |

### Process Improvements Identified

1. **Structure the merge upfront**: Define synthesis schema before running experiments
2. **Track provenance**: Know which insight came from which source
3. **Time-box iterations**: Prevent diminishing returns
4. **Cost awareness**: Budget constraints drove focus
5. **Background execution**: Parallelism dramatically speeds research

### Meta-Learning

The research process itself validated key framework principles:
- **Artifact-centric**: The research doc IS the shared artifact
- **Iteration matters**: Three iterations revealed progressively deeper insights
- **Synthesis is active work**: Not just concatenation, requires integration
- **Diverse perspectives add value**: 4 models × 3 iterations = richer findings

---

## Final Conclusions

### What We Built

A comprehensive framework for multi-model collaborative workflows that:
1. **Generalizes beyond coding** to creative, research, operations, and strategy domains
2. **Provides concrete patterns** with implementation guidance
3. **Includes a practical roadmap** from MVP to production
4. **Identifies AI-native opportunities** beyond human collaboration analogs

### Key Recommendations

**For Immediate Implementation:**
1. Start with blackboard + event log + fixed roles
2. Add turn caps and cost budgets from day 1
3. Instrument for learning before adding learning features
4. Compare against single-model baselines

**For Future Evolution:**
1. Add dynamic routing when you have run history
2. Add resilience when runs become long
3. Add RAG when tasks repeat
4. Explore AI-native patterns (forking, adversarial, failure signals)

### The 10x Opportunity

The research suggests the biggest opportunity isn't better human-like teamwork, but **evolutionary computation on shared artifacts**—where AI systems fork, mutate, test, and evolve solutions in ways humans fundamentally cannot. This requires embracing patterns that feel "wrong" by human standards: massive redundancy, intentional chaos, failure as exploration.

---

## Cost Tracking (Phase 4)

| Experiment | Cost | Cumulative |
|------------|------|------------|
| **Iteration 1** | | |
| Exp 1: Novel patterns | ~$0.08 | $0.08 |
| Exp 2: QA patterns | ~$0.08 | $0.16 |
| Exp 3: Learning patterns | ~$0.08 | $0.24 |
| Exp 4: Workflow stages | ~$0.08 | $0.32 |
| Exp 5: Skills vs roles | ~$0.08 | $0.40 |
| Exp 6: Failure modes | ~$0.08 | $0.48 |
| **Iteration 2** | | |
| Deep Dive 1: Stigmergic | ~$0.20 | $0.68 |
| Deep Dive 2: DYNAMIC-CAP | ~$0.20 | $0.88 |
| Deep Dive 3: RESILIENT | ~$0.18 | $1.06 |
| Deep Dive 4: LEARN | ~$0.12 | $1.18 |
| Deep Dive 5: Test-First | ~$0.30 | $1.48 |
| **Iteration 3** | | |
| Novel Patterns | ~$0.10 | $1.58 |
| Generalized Framework | ~$0.12 | $1.70 |
| Implementation Roadmap | ~$0.12 | $1.82 |
| **Total Phase 4** | **~$1.82** | |
| **Total All Phases** | **~$3.36** | |

Budget remaining: ~$96.64

---

*Iterations 1-3 conducted 2026-01-22.*

---

## Iterations 4-6: Integration with Orchestrator Framework

### Orchestrator Infrastructure Assessment

Based on exploration of Issue #170 and docs/logging_learning_strategy.md (v3.3):

**Existing Infrastructure:**

| Component | Purpose | Status |
|-----------|---------|--------|
| **HealingSupabaseClient** | 3-tier RAG (fingerprint → semantic → causality) | ✅ Active |
| **LearningEngine** | Generate reports, manage LEARNINGS.md | ✅ Active |
| **WorkflowAnalytics** | Phase timing, skip patterns, suggestions | ✅ Active |
| **WorkflowLogger** | Unified logging with learning telemetry | ✅ Active (Issue #155) |
| **EmbeddingService** | OpenAI text-embedding-ada-002 (1536 dim) | ✅ Active |

**Key Architecture Decisions (v3.3):**

1. **Stability Hierarchy:**
   ```
   Workflow YAML (HIGH) → Agent Instructions (MEDIUM) → Runtime (LOW)
   ```

2. **Embed-First Philosophy:**
   - ~80% embed into process (YAML, templates, instructions)
   - ~15-20% runtime injection (ephemeral, per-run)
   - ~5% hybrid (mechanism embedded, data injected)

3. **"AI correlates, human judges"** for effectiveness review

4. **Learning Documentation** requires: what, why, expected outcome

**Mapping Research to Orchestrator:**

| Research Finding | Orchestrator Equivalent | Gap |
|------------------|------------------------|-----|
| LEARN cycle (Log→Exchange→Articulate→Review→Next) | WorkflowLogger + LearningEngine | Missing: Exchange, Articulate pipeline |
| Lesson cards with retrieval | HealingSupabaseClient (errors only) | Partial: Only error patterns, not workflow learnings |
| Reflexion (immediate retry) | Not implemented | Gap |
| Transactive memory | Not implemented | Gap |
| DYNAMIC-CAP skill routing | Not implemented | Gap |
| RESILIENT recovery | Circuit breakers exist | Partial |
| Stigmergic coordination | Workflow state file | Partial: Not multi-agent |

---

### Iteration 4: Integrate Orchestrator Learnings

**Questions Being Explored:**
1. How does existing infrastructure compare to LEARN framework?
2. What's already implemented vs still needed?
3. How does "embed-first" philosophy align with research findings?
4. How to balance YAML stability with dynamic adaptation?
5. What's missing for Learning Crystallization Pipeline (#175)?

**Experiment 1: Infrastructure Comparison (Consensus)**

The orchestrator already has most **plumbing** for LEARN framework:
- Logging ✅ (WorkflowLogger)
- Retrieval ✅ (HealingSupabaseClient 3-tier RAG)
- Embeddings ✅ (EmbeddingService)
- Reporting ✅ (LearningEngine)

**What's Missing:** The **crystallization + governance loop**:
1. **LessonCard schema** (beyond what/why/expected)
2. **Crystallizer** (dedupe/cluster/summarize logs into cards)
3. **Workflow hooks** for injection (phase start, pre-risk, post-failure)
4. **Reflexion→LEARN bridge** (immediate draft → promote if useful)
5. **Governance** (draft→candidate→approved→embedded lifecycle)
6. **Effectiveness scoring** (baselines, success criteria, confidence updates)

**Embed-first aligns with research** IF:
- High-quality, reviewed LessonCards (not raw logs)
- Correct injection points (retrieval becomes behavior change)

---

**Experiment 2: Stability vs Adaptability (Consensus)**

**Tension Resolution:**
- **Stability hierarchy affirmed**: YAML (sacred) > Instructions (medium) > Runtime (ephemeral)
- **Adaptability via injection points**, not YAML mutation
- **Learnings crystallize at appropriate level** based on confidence/evidence

**Key Principle:** "The workflow skeleton is stable; the knowledge injected into it evolves"

---

**Experiment 3: Learning Crystallization Pipeline Gap Analysis (Consensus)**

**Missing Stack:**

```
WorkflowLogger events
       ↓
Episode Reconstructor (group into bounded context windows)
       ↓
Pattern Analyzer / Learning Detector (identify "correction loops", recurring errors)
       ↓
CandidateLesson generation (LLM extraction with structured output)
       ↓
Learning Router (instructions vs issue vs runtime vs discard)
       ↓
Process Embedder (PR/Issue authoring with anchors, dedupe, traceability)
       ↓
Human review gate (never auto-merge)
       ↓
Validation harness (shadow mode, replay, canary)
       ↓
Merge/Promote
```

**Routing Dimensions:** confidence × risk × scope × actionability × stability × impact

---

### Iteration 5: Deep Exploration of Gaps

**Experiment 1: Single to Multi-Agent Evolution (Consensus)**

**First Multi-Agent Capability:** Add **optional verifier/critic** model that reviews primary agent output
- Put behind feature flag
- Keep orchestrator as only tool executor
- Verifier outputs structured (approve/revise + reasons)

**Review Phase as Gateway:** `/review` already uses multi-model (minds)
- Natural place to introduce adversarial patterns
- Proposer/Critic separation maps cleanly

**Blackboard Evolution:**
- Current state file → versioned event log
- Add metadata signals (confidence, provenance)
- Multi-agent coordination as future extension

---

**Experiment 2: LessonCard Schema Design (Consensus)**

**3-Layer Artifact Model:**

```python
# Episode: Raw bounded unit from workflow
class Episode(BaseModel):
    episode_id: str
    workflow_id: str
    start_time: datetime
    end_time: datetime
    goal: str
    tool_traces: list[ToolTrace]
    outcome: Literal["success", "failure", "partial"]
    error_signatures: list[str]
    human_interventions: int

# CandidateLesson: LLM-extracted, not yet approved
class CandidateLesson(BaseModel):
    lesson_id: str
    episode_ids: list[str]  # Evidence links
    what: str               # What to do
    why: str                # Signal/error it addresses
    expected: str           # Expected improvement
    triggers: list[str]     # When to apply
    confidence: float       # 0.0-1.0
    status: Literal["draft", "candidate"]

# LessonCard: Approved, retrievable knowledge
class LessonCard(BaseModel):
    lesson_id: str
    what: str
    why: str
    expected: str
    triggers: list[str]
    evidence_refs: list[str]
    confidence: float
    status: Literal["approved", "embedded", "archived"]
    embedding: list[float]
    dedupe_hash: str        # For exact dedup
    version: int
    application_count: int
    success_rate: float
    created_at: datetime
    last_applied: datetime
```

**Supabase Tables Needed:**
- `episodes` (raw workflow evidence)
- `candidate_lessons` (pre-approval)
- `lesson_cards` (approved, with pgvector index)
- `lesson_applications` (optional: per-use analytics)

---

### Iteration 6: Final Synthesis and Actionable Recommendations

**Consensus: Ship Learning Crystallization MVP first**

#### Immediate Actions (Next 2 Weeks)

**Build Now:**
1. **LessonCard + Episode schemas** (Pydantic)
2. **Supabase tables** (episodes, lessons, pgvector index)
3. **Post-run hook** in orchestrator → trigger lesson extraction
4. **Pre-run hook** → retrieve/inject top-K lessons
5. **Safety controls**: feature flag, kill switch, top-K limits

**Extend Existing:**
- WorkflowLogger: add "finalize episode" hook
- HealingSupabaseClient: add lesson CRUD + vector search
- LearningEngine: owns extraction, dedup, embedding, retrieval

**Defer:**
- Complex multi-agent swarms/debate
- Knowledge graphs / heavy ontology
- Fine-tuning (keep as RAG over validated lessons)

#### Learning System Completion (#175)

**Implementation Order:**
1. DB tables + pgvector + indexes
2. Pydantic schemas + Supabase client methods
3. Retrieval injection path (top-K into prompts)
4. Episode ingestion hook + queue
5. LLM extraction → CandidateLessons + dedup
6. Feedback loop + pruning/retirement

**Success Metrics:**
- Reduced repeat errors
- Fewer user corrections
- Improved first-pass test success
- Retrieval latency <200ms
- Harmful-lesson rate <5%

#### Multi-Model Introduction

**First Capability:** Optional verifier/critic pass
- Feature-flagged
- Structured output (approve/revise)
- Metrics: errors caught pre-delivery, reduced retries

#### Architecture Decisions

**Affirmed:**
- Stability hierarchy (YAML > Instructions > Runtime)
- Embed-first philosophy (with structured lessons, not raw logs)

**New Principles:**
- "Crystallized lessons" as intermediate tier between logs and code
- Never auto-merge learnings (human gate required)
- Shadow/validate before promotion

#### Risk Mitigation

**Risks:**
- Learning pollution (bad lessons)
- Overgeneralization / overfitting
- Context bloat
- Silent regressions

**Mitigations:**
- Quarantine + gates before activation
- Evidence/provenance links
- Top-K injection limits
- Per-lesson disable + global kill switch
- Audit trail of retrieved lesson IDs
- Version pinning/snapshots

---

## Dogfooding Lessons (Iterations 4-6)

| Iteration | Observation | Implication |
|-----------|-------------|-------------|
| 4 | Reading existing codebase first was essential | **Context before creation**: Always understand what exists |
| 4 | Existing infrastructure was more complete than expected | **Don't reinvent**: Assess before designing |
| 5 | Models converged on 3-layer artifact pipeline | **Consensus builds confidence**: Multiple perspectives strengthen design |
| 5 | Disagreements on details (lifecycle states, dedup) are normal | **Track design forks**: Document alternatives for future decisions |
| 6 | Action plan crystallized from synthesis | **Research→Action requires explicit translation**: Don't stop at findings |
| All | Multi-model queries consistently valuable | **Fork-merge validated**: Parallel queries + synthesis works |

---

## Final Cost Tracking

| Phase/Iteration | Experiments | Cost | Cumulative |
|-----------------|-------------|------|------------|
| **Iterations 1-3** | 14 experiments | ~$1.82 | $1.82 |
| **Iteration 4** | 3 experiments | ~$0.60 | $2.42 |
| **Iteration 5** | 2 experiments | ~$0.40 | $2.82 |
| **Iteration 6** | 1 experiment | ~$0.20 | $3.02 |
| **Total Phase 4** | **20 experiments** | **~$3.02** | |
| **Total All Phases** | | **~$4.56** | |

Budget remaining: ~$95.44

---

*Iterations 4-6 conducted 2026-01-22. Full integration with orchestrator framework completed.*

