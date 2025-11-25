# Sprint 5 Persistence: Critical Technology Review

## 🔍 Purpose
Challenge our technology choices with hard questions before committing to implementation. Better to discover issues now than after building.

---

## 🎯 Critical Questions

### 1. SQLite: Right Tool for Scientific Data?

#### The Case FOR SQLite
- **Scientific workflows are often single-user** - One researcher analyzing their data
- **Beamline computers are isolated** - Not always networked, SQLite works offline
- **Simplicity wins** - No DBA, no server, just works
- **Portability is critical** - Can email entire database to collaborator
- **JSON support in SQLite** - Good for flexible metadata storage

#### The Case AGAINST SQLite
- **NFS/network storage issues** - Many labs use NFS home directories
  - SQLite uses file locking that breaks on NFS
  - Could corrupt database if accessed from multiple machines
  - **Question**: Where do RoboMage users actually store data?

- **Limited concurrent access** - Only one writer at a time
  - **Question**: Will users want to run batch analysis while browsing dashboard?
  - Background analysis service could block dashboard updates

- **No built-in replication** - Can't easily sync across machines
  - **Question**: Do users work on multiple computers (office + beamline)?

- **Schema evolution complexity** - Migrations are harder without server
  - What if user has old database version?
  - Need robust migration strategy

#### 🚨 **Key Decision Point**
**Where do NSLS-II users actually store their data?**
- Local SSD? ✅ SQLite perfect
- NFS home directory? ⚠️ SQLite risky
- Shared lab server? ❌ Need PostgreSQL

**Action Required**: Survey actual user storage patterns before committing.

---

### 2. Do We Need an ORM at All?

#### The Case FOR SQLAlchemy
- Type safety and validation
- Database agnostic (SQLite → PostgreSQL migration)
- Query builder prevents SQL injection
- Good for complex joins and relationships

#### The Case AGAINST SQLAlchemy
- **Adds complexity** - Learning curve, debugging ORM issues
- **Performance overhead** - ORM layer adds latency
- **Overkill for simple queries** - Most queries are straightforward
- **RoboMage already has Pydantic models** - Do we need two model layers?

#### Alternative: Pydantic + Raw SQL
```python
# Simpler approach:
@dataclass
class Session:
    id: int
    name: str
    created_at: datetime

# Direct SQL with Pydantic validation
def get_session(db, session_id: int) -> Session:
    row = db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    return Session(**row)
```

**Pros:**
- Single source of truth (Pydantic models)
- Less magic, easier to debug
- Faster queries
- Smaller dependency footprint

**Cons:**
- Manual SQL writing
- No query builder safety
- Manual migrations
- More boilerplate

#### 🚨 **Key Decision Point**
**Is the ORM complexity justified for RoboMage's query patterns?**

Most queries are simple:
- Get session by ID
- List files in session
- Find cached analysis

Complex joins are rare. Do we need SQLAlchemy's power?

**Alternative approach**: Start with raw SQL + Pydantic, add SQLAlchemy only if needed.

---

### 3. Session-Based Model: Does It Match User Workflow?

#### Assumed Workflow (Our Design)
```
User opens dashboard
→ Creates/loads "session" 
→ Uploads files to session
→ Analyzes files
→ Saves session
→ Closes dashboard
```

#### Actual Workflow (Hypothesis to Validate)
**Scenario A: Quick Analysis**
```
User has .chi file from beamline
→ Opens dashboard
→ Drag-drops file
→ Runs peak analysis
→ Exports figure for paper
→ Closes (never thinks about "sessions")
```
**Problem**: Session concept adds friction for quick tasks.

**Scenario B: Batch Processing**
```
User has 100 .chi files from overnight run
→ Wants to analyze all
→ Compare trends
→ Generate report
```
**Problem**: Does "session" == "batch"? Or separate concepts?

**Scenario C: Long-term Project**
```
User analyzes LaB6 every month for calibration
→ Wants to track drift over time
→ Compare this month to historical data
```
**Problem**: Multiple sessions per project? How to organize?

#### 🚨 **Key Decision Point**
**Is "session" the right organizing principle?**

**Alternative models to consider:**

**Option A: Implicit Sessions (Auto-Save Everything)**
- No explicit session creation
- Auto-create session on first file upload
- Session = day's work (auto-named "2025-11-25")
- User can rename/organize later

**Option B: Project-Based Organization**
```
Project: "LaB6 Calibration"
├── Dataset: "2025-11-25"
│   ├── file1.chi
│   └── file2.chi
├── Dataset: "2025-12-01"
└── Reports/
```

**Option C: Tag-Based (No Sessions)**
- Files are just files
- Tags for organization
- Queries like "Show me all LaB6 files"

**Question**: Which model matches how scientists actually think about their data?

---

### 4. File Storage: Where and How?

#### Proposed: `~/.robomage/files/`

**Concerns:**
1. **Disk space**: Diffraction files can be large, many files = many GB
   - User's home directory might have quota limits
   - **Question**: Should we make storage location configurable?

2. **Deduplication**: Store same file uploaded to multiple sessions?
   - Hash-based deduplication saves space
   - But complicates deletion (reference counting needed)
   - **Question**: Worth the complexity?

3. **File organization**: How to structure?
   ```
   Option A: By session
   files/sessions/{session_id}/{filename}
   + Easy to delete session (rm -rf)
   - Hard to deduplicate
   
   Option B: Content-addressed (by hash)
   files/objects/{hash[:2]}/{hash}
   + Perfect deduplication
   + Can't accidentally corrupt
   - Can't browse easily
   - Needs garbage collection
   
   Option C: Hybrid
   files/sessions/{session_id}/{filename}  (symlinks)
   files/objects/{hash}                    (real files)
   + Best of both worlds
   - More complexity
   ```

#### Alternative: Don't Store Files at All

**Radical option**: Just store file paths
```python
# Instead of copying files:
File(
    session_id=1,
    filename="sample.chi",
    original_path="/data/beamline/run123/sample.chi",  # Don't copy
    wavelength=0.1665
)
```

**Pros:**
- No disk space needed
- No file copying
- Single source of truth

**Cons:**
- Files might move/delete
- Can't share sessions (paths invalid on other machines)
- Doesn't work for uploaded files

**Hybrid approach:**
- Uploaded files: store in `~/.robomage/`
- Batch analysis: store references only
- User chooses per use case

#### 🚨 **Key Decision Point**
**File storage strategy significantly impacts complexity and UX.**

**Questions to answer:**
- Do users need portable sessions?
- Is disk space a concern?
- Are files typically moved/deleted after analysis?

---

### 5. Caching Strategy: Automatic or Manual?

#### Proposed: Automatic Caching
Every analysis auto-saves to database, cache hit on exact parameter match.

**Concerns:**
1. **Parameter matching is fuzzy** 
   ```python
   params1 = {"prominence": 0.1, "distance": 5}
   params2 = {"distance": 5, "prominence": 0.1}  # Same? Different order
   params3 = {"prominence": 0.10, "distance": 5}  # Same? Float precision
   ```
   Need robust parameter normalization.

2. **Cache invalidation**
   - What if peak analysis algorithm improves?
   - Old cached results are now wrong
   - Need version tracking in cache

3. **Cache bloat**
   - Many slightly different parameter sets = many cached results
   - Database grows indefinitely
   - Need cache eviction policy

4. **User expectations**
   - User changes prominence 0.1 → 0.11 → 0.1
   - Expects new analysis, gets cache?
   - Need UI indicator of cache hit

#### Alternative: Explicit Save/Load
```python
# User explicitly saves "good" analyses
analysis = run_peak_analysis(...)
if user_likes_it:
    save_analysis(name="Final LaB6 Analysis", ...)

# Later, user loads saved analyses
analyses = list_saved_analyses(session_id)
```

**Pros:**
- User control
- Only "good" results saved
- Clearer UX

**Cons:**
- Extra user steps
- Might forget to save

#### 🚨 **Key Decision Point**
**Automatic caching is complex. Is it worth it?**

**Alternative**: 
- Phase 1: No automatic caching, just session/file storage
- Phase 2: Add caching once we understand usage patterns

**Question**: Do users frequently re-run identical analyses? Or is each analysis unique?

---

### 6. Alembic Migrations: Necessary Evil or Overkill?

#### The Case FOR Alembic
- Professional schema evolution
- Rollback support
- Auto-generation from model changes

#### The Case AGAINST Alembic
- **Adds complexity** - Another tool to learn
- **Users won't run migrations** - They'll just get errors
- **SQLite makes it harder** - No ALTER TABLE support for many operations

#### Alternative: Versioned Database Files
```python
# Check database version on startup
db_version = get_db_version()
if db_version < CURRENT_VERSION:
    # Run simple upgrade SQL
    upgrade_database(db_version)
```

**Simpler approach:**
```python
# Version 1 → 2 migration
if db_version == 1:
    db.execute("ALTER TABLE sessions ADD COLUMN tags JSON")
    set_db_version(2)
```

**Or even simpler: Graceful degradation**
```python
# Try new column, fall back if missing
try:
    tags = session.tags
except AttributeError:
    tags = []  # Old database, no tags column
```

#### 🚨 **Key Decision Point**
**How often will schema change in practice?**

If schema is stable after initial implementation, Alembic is overkill.
If schema evolves frequently, Alembic saves pain.

**Question**: How mature is RoboMage's data model?

---

### 7. Multi-User Support: Design for It Now or Later?

#### Proposed: SQLite (Single-User)
But design allows PostgreSQL migration.

**Questions:**
1. **How much design is enough?**
   - Single DB connection? Or connection pooling?
   - User ID in all tables? Or add later?
   - Authentication/authorization? Or skip?

2. **YAGNI vs Future-Proofing**
   - You Ain't Gonna Need It: Build for today's needs
   - But: Refactoring database layer is painful

3. **Is multi-user actually needed?**
   - Shared analysis sessions between researchers?
   - Collaborative peak annotation?
   - Or is emailing .db files sufficient?

#### 🚨 **Key Decision Point**
**How much to design for multi-user now?**

**Options:**
- **Minimal**: Pure single-user, refactor if needed later
- **Prepared**: Add user_id columns (default='local'), abstraction layer
- **Full**: Build for multi-user from start (PostgreSQL, auth)

**Recommendation**: Middle ground - add user_id fields but don't implement auth yet.

---

### 8. Configuration: Where Should Database Live?

#### Proposed: `~/.robomage/robomage.db`

**Concerns:**
1. **Hidden directory** - Users might not find it
2. **Not portable** - Can't have per-project databases
3. **Backup** - Users won't think to backup hidden dirs

#### Alternatives:

**Option A: Project-Local Database**
```
/data/my-analysis/
├── data/
│   └── sample.chi
└── .robomage.db  # Database in project directory
```
**Pros**: Portable, obvious, backs up with data
**Cons**: Multiple databases to manage

**Option B: Configurable Location**
```python
# Environment variable or config file
ROBOMAGE_DB_PATH=/data/shared/robomage.db
```
**Pros**: Flexible
**Cons**: Configuration burden

**Option C: Ask on first run**
```
RoboMage first run detected!
Where should we store your analysis database?
1. Home directory (~/.robomage/)
2. Current directory
3. Custom location
```

#### 🚨 **Key Decision Point**
**Database location affects UX and data safety.**

**Question**: What's the most user-friendly default that minimizes data loss risk?

---

## 🎯 Decision Framework

For each decision, rate:
1. **Complexity**: How much harder does this make implementation?
2. **User Impact**: How much does this affect daily usage?
3. **Reversibility**: How hard to change later?
4. **Evidence**: Do we have data to support this choice?

### Example Scorecard

| Decision | Complexity | User Impact | Reversibility | Evidence | Recommendation |
|----------|-----------|-------------|---------------|----------|----------------|
| SQLite vs PostgreSQL | Low | High | Hard | ❌ Need data | Survey users first |
| SQLAlchemy vs Raw SQL | High | Low | Medium | ✅ Known patterns | Start simple, add ORM if needed |
| Auto-caching | High | Medium | Medium | ❌ Need usage data | Phase 2 feature |
| Session model | Medium | High | Hard | ❌ Need validation | Prototype & user test |
| Alembic migrations | Medium | Low | Easy | ✅ Schema likely stable | Skip for now |

---

## 🚀 Recommended Approach: Incremental

### Phase 0: Validation (Before Building)
**Duration: 1-2 days**

1. **User Research**
   - Survey 3-5 actual RoboMage users (or potential users)
   - Questions:
     - Where do you store diffraction data? (Local/NFS/Server)
     - How do you organize analysis work? (Projects/Dates/Tags)
     - Do you re-analyze same files often?
     - Would you use sessions or prefer automatic tracking?

2. **Prototype Testing**
   - Build minimal proof of concept (raw SQLite + Pydantic)
   - Test with real .chi files from NSLS-II
   - Measure:
     - Query performance
     - Database size growth
     - Common usage patterns

3. **Architecture Decision Record (ADR)**
   - Document each major decision
   - Record rationale and trade-offs
   - Easier to revisit later

### Phase 1: Minimal Viable Persistence (MVP)
**Duration: 3 days**

**Scope:**
- ✅ SQLite database (simplest)
- ✅ Raw SQL + Pydantic models (no ORM)
- ✅ Session, File, Analysis tables only (no Peaks table yet)
- ✅ Store file metadata only (don't copy files yet)
- ✅ Manual save/load (no auto-caching)
- ✅ Fixed location: `~/.robomage/robomage.db`
- ❌ No migrations (manual SQL for schema changes)
- ❌ No multi-user support

**Goal**: Prove the concept with minimal complexity.

### Phase 2: Refinement (Based on MVP Learning)
**Duration: 2-3 days**

**Add based on what we learn:**
- File storage (if needed)
- Automatic caching (if valuable)
- SQLAlchemy (if queries get complex)
- Peak table (if comparison features needed)
- Migrations (if schema changes frequently)

### Phase 3: Production Hardening
**Duration: 2 days**

- Error handling
- Database corruption recovery
- Export/import for sharing
- Documentation

---

## 📋 Questions to Answer Before Starting

### Must Answer (Blocking)
1. ❓ **Where do NSLS-II users store data?** (Affects SQLite viability)
2. ❓ **How do users organize their work?** (Affects session model)
3. ❓ **Do users re-analyze files often?** (Affects caching priority)

### Should Answer (Important)
4. ❓ **Do users work on multiple machines?** (Affects portability needs)
5. ❓ **How large are typical .chi files?** (Affects storage strategy)
6. ❓ **How many files in typical analysis?** (Affects performance needs)

### Nice to Answer (Informative)
7. ❓ **Would users share sessions with colleagues?** (Affects multi-user priority)
8. ❓ **Do users need long-term archival?** (Affects database design)

---

## 🎯 Next Steps

### Option A: Proceed with Original Design
**If**: We're confident in our assumptions
**Risk**: Build wrong thing, have to refactor
**Mitigation**: Keep design modular, use abstraction layers

### Option B: Validate First (RECOMMENDED)
**Steps**:
1. Create user survey (1 day)
2. Build minimal prototype (2 days)
3. Test with real users (2 days)
4. Revise design based on feedback (1 day)
5. Start implementation with confidence

**Total time**: +6 days
**Benefit**: Build the right thing

### Option C: Simplified First Version
**Steps**:
1. Implement absolute minimum (Phase 1 MVP above)
2. Ship to early users
3. Learn from real usage
4. Iterate based on data

**Benefit**: Fastest path to learning

---

## 💡 Recommendations

### Immediate Actions
1. ✅ **Create this review document** (Done)
2. 🔄 **Discuss with team/users** - Which assumptions are risky?
3. 🔄 **Decide on approach** - Original, Validate, or Simplified?
4. 🔄 **Answer blocking questions** - Can't proceed without this data

### Technology Recommendations
Based on conservative risk assessment:

**Start Simple:**
- ✅ SQLite (but validate storage location first)
- ✅ Raw SQL + Pydantic (add ORM only if needed)
- ✅ Manual save/load (auto-caching in Phase 2)
- ✅ No migrations initially (add Alembic when schema stabilizes)
- ✅ File metadata only (copy files later if needed)

**Rationale**: Build minimum to learn, add complexity when justified by evidence.

---

## 🤔 Final Question

**Before we write any code: What don't we know that could invalidate this design?**

List risks and mitigation:
1. **Risk**: Users store on NFS → SQLite corrupts
   **Mitigation**: Survey storage patterns first
   
2. **Risk**: Session model doesn't match workflow
   **Mitigation**: Prototype and user test
   
3. **Risk**: Caching is more complex than valuable
   **Mitigation**: Phase 2 feature, measure need first

4. **Risk**: Database grows too large
   **Mitigation**: Benchmark with realistic data

5. **Risk**: Users never use persistence features
   **Mitigation**: MVP validation before full build

---

**Document Status**: Ready for critical review and decision meeting
**Next Step**: Team discussion of approach (Option A/B/C)
