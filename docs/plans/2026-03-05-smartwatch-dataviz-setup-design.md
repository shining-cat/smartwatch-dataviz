# Smartwatch Data Visualization Tool - Setup & Multi-Agent Learning Design

**Date:** 2026-03-05
**Status:** Approved
**Purpose:** Bootstrap health data visualization project with proper foundation while learning multi-agent development patterns

## Project Goals

### Primary Goal
Learn multi-agent workflow through hands-on development using Claude Code's sub-agent system.

### Secondary Goal
Build a privacy-first health data visualization tool that provides better insights than proprietary smartwatch dashboards.

### Success Criteria
- ✅ Git-tracked project with strict data privacy (never commit health data)
- ✅ Enhanced validation workflow (automated data testing before manual verification)
- ✅ Working Sleep Deep Dive feature built via multi-agent coordination
- ✅ Understanding of agent decomposition, coordination, and mechanics
- ✅ Extensible foundation for future feature development

## Key Constraints

1. **Privacy First:** Health data never leaves local machine, never committed to git
2. **OS Portability:** Must work identically on macOS (work) and Windows 11 (personal)
3. **No Brand Names:** Never reference specific hardware brands in committed code
4. **Learning Priority:** Multi-agent learning takes precedence over shipping all features
5. **Defensive Coding:** Prefer graceful degradation, helpful error messages, no crashes

## Architecture Decisions

### Project Structure
```
__DEV/PERSO/smartwatch-dataviz/
├── index.html          # Single-file app (selective keep + rebuild)
├── data/               # .gitignored - all health data lives here
│   └── raw/
│       └── export.zip  # User's health export
├── docs/
│   ├── plans/          # Design docs, implementation plans
│   └── README.md       # Setup instructions, usage guide
└── .gitignore          # Blocks data/**, temp files, OS files
```

### Single-File HTML Approach

**Decision:** Keep single-file HTML architecture (at least initially).

**Rationale:**
- Perfect cross-platform portability (just needs a browser)
- Zero dependencies, zero build step
- Easy to transfer between machines (one file)
- Double-click to run (no local server needed)
- Current size (~1126 lines) is manageable
- Can split later if it becomes unwieldy (3000+ lines)

**Trade-offs Accepted:**
- Harder to maintain as code grows
- All code in one file (HTML + CSS + JS)
- No module system benefits

### Data Safety Strategy

**.gitignore coverage:**
```gitignore
# Health data - NEVER commit
data/**/*
!data/.gitkeep
!data/*/.gitkeep

# Backup/temp files
*.bak
*.tmp
*~

# OS files
.DS_Store
Thumbs.db
```

**Verification:**
- Before first commit: explicit `git status` review
- README documents: "Place health export in `data/raw/`"
- Repository can be made public safely (no PII in tracked files)

### Validation Workflow (Anti-Drift)

**Problem Solved:** ChatGPT made blind changes with no validation loop → inconsistent versions.

**Three-Layer Validation:**

**Layer 1: Data Validation (Automated)**
- Claude parses actual health export ZIP
- Tests data processing logic against real data
- Catches: parsing errors, missing fields, type issues, edge cases
- Output: "✓ Processed 847 days, metrics: steps, sleep, HR..."

**Layer 2: Code Validation (Automated)**
- Syntax checking
- Logic flow verification
- Runtime error simulation
- Catches: JS errors, null references, logic bugs

**Layer 3: Rendering Validation (Manual)**
- User opens in browser
- Verifies visual appearance, UX, chart rendering
- Catches: visual bugs, layout issues, interaction problems

**Iteration Flow:**
```
Edit → Data Test → Code Test → Browser Verify → Commit (if good) → Repeat
```

**Why This Works:**
- ~80% of bugs caught before manual testing
- Small, frequent iterations with validation checkpoints
- Git history provides version safety net
- User focuses on UX/visual QA, not hunting data bugs

## Code Foundation Strategy

### Selective Keep Approach

**Keep from Current Implementation:**
- ✅ Data parsing logic (CSV parsing, ZIP extraction)
- ✅ File format detection (aggregates, sleep, weight)
- ✅ IndexedDB storage layer
- ✅ Basic UI structure (drag-drop, file loading)
- ✅ Timeline & Weekly Seasonality tabs (working features)

**Rebuild with Defensive Patterns:**
- 🔨 Error handling (graceful degradation)
- 🔨 Input validation (null checks, edge cases)
- 🔨 User feedback (helpful error messages, loading states)
- 🔨 Sleep tab → completely new Sleep Deep Dive implementation

**Rationale:**
- Parsing logic is battle-tested (don't reinvent wheel)
- Shows quick results (existing tabs still work)
- Foundation improvements happen incrementally
- Fire test builds greenfield Sleep Deep Dive

## Three-Phase Implementation Plan

### Phase 1: Foundation Setup (Solo - ~10 minutes)

**Objectives:**
- Establish clean project structure
- Initialize version control with data safety
- Validate baseline functionality

**Actions:**
1. Move project from Downloads to `__DEV/PERSO/smartwatch-dataviz/`
2. Initialize git repository
3. Create `.gitignore` with data blocking
4. Move health export ZIP to `data/raw/`
5. Create directory structure (`docs/`, `data/raw/`)
6. Validate current `index.html` still works
7. First commit: "Initial project setup"

**Multi-Agent Learning:** None (baseline establishment)

**Output:** Clean, git-tracked project ready for development

---

### Phase 2: Data Deep-Dive (Single Exploration Agent - ~15 minutes)

**Objectives:**
- Understand available metrics and data structure
- Identify data quality issues
- Learn single-agent exploration pattern

**Agent Task:**
"Analyze health export ZIP structure. Document all available metrics, date ranges, data quality issues, and file formats. Provide comprehensive inventory for feature planning."

**Multi-Agent Learning Demonstration:**

1. **Agent Briefing** - How to write specific, actionable instructions
2. **Isolated Context** - Agent explores without cluttering main conversation
3. **Report-Back Pattern** - How agents communicate findings
4. **When to Delegate** - Exploration vs doing analysis yourself

**Output:**
- Documented data structure (what files exist, what they contain)
- Metrics inventory (steps, sleep duration, HR, HRV, etc.)
- Date range coverage (first/last measurement dates)
- Data quality notes (gaps, anomalies, parsing challenges)
- Foundation for Phase 3 feature decisions

---

### Phase 3: Sleep Deep Dive Feature (3 Parallel Agents - ~30 minutes)

**Objectives:**
- Build meaningful feature using coordinated agents
- Learn decomposition, coordination, and integration patterns
- Deliver working Sleep Deep Dive tab

**Feature Scope: Sleep Deep Dive Tab**

Three sub-features, each built by separate agent:

**Agent 1: Sleep Duration Analysis**
- Parse sleep session data
- Calculate: distribution, average, variance, percentiles
- Generate histogram data structure
- Code: duration calculation functions + histogram visualization

**Agent 2: Sleep Timing Patterns**
- Extract bedtime and wake time from sessions
- Calculate consistency scores (standard deviation)
- Detect chronotype indicators (early bird vs night owl)
- Code: timing analysis functions + scatter plot visualization

**Agent 3: Weekly Pattern Detection**
- Compute weekday sleep duration averages
- Detect office day effects (if user tags specific weekdays)
- Calculate weekend vs weekday comparison
- Code: pattern detection functions + comparison visualization

**Coordination Challenges (Learning Opportunities):**

1. **Shared Dependencies**
   - All agents need consistent sleep data parsing
   - Need common date/time utilities
   - Coordinate on data structure contracts

2. **Integration Point**
   - Three separate visualizations → single cohesive tab
   - Consistent styling and layout
   - Proper error handling if one component fails

3. **Parallel Execution**
   - Agents work simultaneously on independent code
   - Main thread integrates results
   - Handle potential conflicts or assumptions

**Multi-Agent Learning Demonstration:**

1. **Work Decomposition** - How to break feature into parallelizable tasks
2. **Clear Boundaries** - What makes good agent task boundaries
3. **Coordination Strategy** - Managing dependencies and shared code
4. **Conflict Avoidance** - Preventing agents from stepping on each other
5. **Integration Pattern** - Assembling parallel work into cohesive feature
6. **Monitoring & Debugging** - Tracking agent progress, handling failures

**Output:**
- Working Sleep Deep Dive tab with three interactive visualizations
- Hands-on experience with multi-agent coordination
- Code patterns for future feature development
- Understanding of when/how to use parallel agents

## Future Extensibility

### Designed for Growth
This foundation supports future features without major refactoring:

**Next Feature Candidates:**
- Correlation Lab (correlation matrix, lagged correlations)
- Activity Intelligence (trend detection, streak tracking)
- Temporal Pattern Intelligence (seasonal effects, recurring events)
- Recovery Modeling (HRV + HR + sleep composite scoring)

**Multi-Agent Patterns Established:**
- Exploration agents for research/analysis
- Parallel agents for independent feature components
- Coordination strategies for integration

**Development Workflow:**
- Design → Multi-agent implementation → Data validation → Browser verification → Commit

## Technical Stack

**Runtime:** Browser (Chrome, Firefox, Safari, Edge)
**Data Processing:** JavaScript (ES6+)
**Parsing:** PapaParse (CSV), JSZip (ZIP archives)
**Storage:** IndexedDB (Dexie.js)
**Visualization:** ECharts
**Development:** Git, single-file HTML architecture

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Health data leaked to git | Strict `.gitignore`, pre-commit verification |
| Code drift without validation | Three-layer validation (data, code, rendering) |
| Single-file becomes unmaintainable | Monitor size, split at 3000+ lines if needed |
| Multi-agent coordination complexity | Start simple (1 agent), progress to parallel (3 agents) |
| Platform portability breaks | Stick to web standards, test on both macOS/Windows |

## Non-Goals (Explicitly Out of Scope)

- ❌ Backend server (stays 100% client-side)
- ❌ Multi-user support (single-user tool)
- ❌ Cloud sync (local-only, manual file transfer between machines)
- ❌ Mobile app (browser-based is sufficient)
- ❌ Weight/calorie tracking (user not interested)
- ❌ Advanced ML/forecasting (keep it simple, interpretable)

## Success Metrics

**Learning Outcomes:**
- [ ] Understand how to decompose work for multi-agent execution
- [ ] Understand coordination patterns (dependencies, integration)
- [ ] Understand when to use agents vs solo work
- [ ] Comfortable briefing agents with specific instructions
- [ ] Can apply patterns to future projects

**Technical Outcomes:**
- [ ] Project runs identically on macOS and Windows 11
- [ ] `git status` never shows data files (verified safety)
- [ ] Sleep Deep Dive tab shows three working visualizations
- [ ] No crashes on malformed/missing data (defensive coding)
- [ ] Code changes validate against real data before manual testing

**Project Outcomes:**
- [ ] Better insights than proprietary dashboard (subjective but valuable)
- [ ] Foundation ready for future feature development
- [ ] Project structure supports long-term maintenance
