# SQLite vs PostgreSQL: Decision Analysis for RoboMage

**Decision Date**: November 25, 2025  
**Context**: Choosing database technology for Sprint 5 persistence layer  
**Status**: Recommendation pending

---

## 🎯 Executive Summary

**TL;DR Recommendation**: **Start with SQLite**, but design abstraction layer for future PostgreSQL migration.

**Key Insight**: RoboMage's current architecture is **local-first** (localhost services, single-user dashboard), making SQLite the natural fit. PostgreSQL becomes valuable only if RoboMage evolves into a shared facility service.

---

## 📊 Decision Framework: Realistic Scenarios

### Scenario Analysis Method
Instead of abstract pros/cons, let's evaluate based on **actual deployment scenarios** for RoboMage at NSLS-II:

```
Scenario A: Individual Scientist Workstation (Current Reality)
Scenario B: Shared Beamline Computer (Potential)
Scenario C: Facility-Wide Analysis Service (Future Vision)
```

---

## 🔬 Scenario A: Individual Scientist Workstation

### Description
- Scientist runs RoboMage on their local workstation
- Analyzes their own experimental data from beamline
- Dashboard runs locally (`http://localhost:8050`)
- Peak analysis service runs locally (`http://localhost:8001`)
- Data stored in home directory or local project folder

### SQLite Analysis for Scenario A

**Advantages** ✅
1. **Zero Configuration**
   - No database server to install/configure
   - No port conflicts, no authentication setup
   - Just works after `pixi install`
   - Critical for scientists (not DBAs)

2. **Perfect for Local-First**
   - Database is a single file (portable)
   - Can email `robomage.db` to collaborator
   - Backup = copy file
   - Version control friendly (can track in git for small DBs)

3. **Performance for Single User**
   - **Faster** than PostgreSQL for read-heavy workloads
   - No network overhead (even localhost has latency)
   - Typical query benchmarks:
     ```
     SQLite:     0.1-1ms (local file I/O)
     PostgreSQL: 1-5ms (localhost TCP + parsing)
     ```

4. **Offline Operation**
   - Works without network (important at beamlines)
   - No server process that can crash
   - No dependencies on facility IT infrastructure

5. **Simplicity**
   - Built into Python standard library
   - No additional pixi dependencies
   - Smaller attack surface
   - Easier debugging (just open .db file)

**Disadvantages** ⚠️
1. **Concurrent Write Limitation**
   - Only one writer at a time
   - **Impact**: If dashboard is running AND batch CLI analysis
   - **Reality**: Scientist typically does one thing at a time
   - **Mitigation**: Modern SQLite has WAL mode (better concurrency)

2. **No Network Access**
   - Database locked to local machine
   - **Impact**: Can't access from office computer
   - **Reality**: Scientist works on one machine, or copies .db file
   - **Mitigation**: Export/import functionality

3. **File Locking on NFS**
   - **Critical Risk**: Corruption if database on network drive
   - **Impact**: If `~/.robomage/` is on NFS home directory
   - **Investigation Needed**: Where do NSLS-II users actually store data?

**Verdict for Scenario A**: ✅ **SQLite is EXCELLENT**
- Matches local-first architecture perfectly
- Zero friction for scientist users
- Performance is better than PostgreSQL
- Only concern: NFS file locking (needs investigation)

---

## 🖥️ Scenario B: Shared Beamline Computer

### Description
- Multiple scientists use same beamline computer
- Each scientist analyzes their data during beam time
- Users might overlap (one analyzing while another collects)
- Shared environment, but isolated workflows

### SQLite Analysis for Scenario B

**Concurrent Access Patterns**:
```
User 1: Running dashboard (read-heavy, occasional writes)
User 2: Running batch CLI analysis (write-heavy)
User 3: Browsing old sessions (read-only)
```

**SQLite with WAL Mode** (Write-Ahead Logging)
```python
# Enable WAL mode for better concurrency
PRAGMA journal_mode=WAL;

# Performance characteristics:
# - Multiple readers: NO BLOCKING ✅
# - Reader + writer: NO BLOCKING ✅ (reader sees old data)
# - Multiple writers: BLOCKING ⚠️ (serialized)
```

**Advantages** ✅
1. **Per-User Databases**
   - Each user has own `.robomage/robomage.db`
   - No concurrent access issues
   - Clear data ownership
   - Privacy maintained

2. **Still Simple**
   - No server administration on beamline computer
   - No port conflicts between users
   - No shared credentials to manage

**Disadvantages** ⚠️
1. **No Cross-User Queries**
   - Can't compare User A's results with User B's
   - Each scientist has isolated data
   - **Question**: Do beamline users need to share data in real-time?

2. **Potential Write Conflicts**
   - If users share database file (not recommended)
   - Concurrent writes would serialize
   - **Mitigation**: Don't share database files

**Verdict for Scenario B**: ✅ **SQLite is GOOD**
- Per-user databases solve concurrency
- Simplicity is valuable on shared computers
- Only limitation: no real-time collaboration
- PostgreSQL would enable sharing, but adds complexity

---

## 🏢 Scenario C: Facility-Wide Analysis Service

### Description
- RoboMage deployed as centralized service
- Multiple beamlines access shared analysis platform
- Web-based dashboard accessible from anywhere
- Collaborative features: shared sessions, team analysis
- Data provenance and audit requirements

### PostgreSQL Analysis for Scenario C

**Advantages** ✅
1. **True Multi-User Concurrency**
   - MVCC (Multi-Version Concurrency Control)
   - Many concurrent readers and writers
   - No blocking on reads
   - Proper transaction isolation

2. **Centralized Data**
   - All beamlines access same database
   - Cross-beamline comparisons possible
   - Facility-wide statistics and reporting
   - Centralized backups

3. **Advanced Features**
   - User authentication and authorization
   - Row-level security
   - Sophisticated query optimization
   - Better indexing for complex queries
   - Full-text search
   - Geospatial capabilities (if needed)

4. **Operational Maturity**
   - Enterprise monitoring tools
   - Hot backups without downtime
   - Replication for high availability
   - Point-in-time recovery

5. **Scalability**
   - Handles TB-scale databases
   - Can scale to thousands of users
   - Performance tuning options

**Disadvantages** ⚠️
1. **Operational Overhead**
   - Requires DBA or DevOps support
   - Server installation and configuration
   - Backup strategy and monitoring
   - Security hardening
   - Version upgrades

2. **Network Dependency**
   - Service unavailable if network down
   - Latency for remote users
   - VPN required for off-site access
   - Not suitable for offline beamline computers

3. **Complexity**
   - Connection pooling configuration
   - Authentication setup
   - SSL/TLS certificates
   - More things that can break

4. **Resource Requirements**
   - Dedicated server or container
   - Memory for connections (each ~10MB)
   - Storage for database files
   - Monitoring infrastructure

**SQLite Disadvantages for Scenario C** ❌
1. **Single Writer Limitation**
   - Many concurrent analyses would queue
   - Dashboard updates would block batch jobs
   - Unacceptable user experience

2. **No Network Access**
   - Can't support web-based multi-user dashboard
   - Each user would need local installation

3. **No User Management**
   - Can't implement permissions
   - Can't audit who changed what
   - Security concerns

**Verdict for Scenario C**: ✅ **PostgreSQL is REQUIRED**
- Multi-user concurrency is essential
- Centralized architecture demands it
- SQLite architecturally wrong for this use case

---

## 🔍 Technical Deep Dive: Performance Comparison

### Benchmark Context
Using RoboMage's expected workload:
- Sessions table: ~1000 rows/user
- Files table: ~10,000 rows/user
- Analyses table: ~50,000 rows/user
- Peaks table: ~500,000 rows/user (10 peaks/analysis)

### Read Performance (Typical Dashboard Query)

**Query**: Load session with all files and latest analyses
```sql
SELECT s.*, f.*, a.*
FROM sessions s
JOIN files f ON f.session_id = s.id
LEFT JOIN analyses a ON a.file_id = f.id
WHERE s.id = 123
ORDER BY a.timestamp DESC
LIMIT 100;
```

**SQLite** (local file):
- Cold cache: 5-20ms
- Warm cache: 0.5-2ms
- **Advantage**: Direct file I/O, no network/parsing

**PostgreSQL** (localhost):
- Cold cache: 10-30ms
- Warm cache: 2-5ms
- **Overhead**: TCP connection, query parsing, protocol

**Winner for single-user reads**: ✅ **SQLite** (2-3x faster)

### Write Performance (Save Analysis Results)

**Query**: Insert analysis + 15 peaks (transaction)
```sql
BEGIN;
INSERT INTO analyses (...) VALUES (...);
INSERT INTO peaks (...) VALUES (...);  -- 15 rows
COMMIT;
```

**SQLite** (WAL mode):
- Transaction time: 1-5ms
- Throughput: 200-1000 writes/sec
- **Limitation**: Only one writer at a time

**PostgreSQL**:
- Transaction time: 2-8ms
- Throughput: 100-500 writes/sec (single connection)
- Throughput: 1000+ writes/sec (multiple connections)
- **Advantage**: Multiple concurrent writers

**Winner for single-writer**: ✅ **SQLite** (slightly faster)  
**Winner for multi-writer**: ✅ **PostgreSQL** (scales with connections)

### Complex Query Performance (Historical Analysis)

**Query**: Find all peaks near d-spacing across all sessions
```sql
SELECT p.*, a.*, f.filename, s.name
FROM peaks p
JOIN analyses a ON a.id = p.analysis_id
JOIN files f ON f.id = a.file_id
JOIN sessions s ON s.id = f.session_id
WHERE p.d_spacing BETWEEN 2.99 AND 3.01
  AND a.timestamp > '2025-01-01'
ORDER BY p.fit_quality DESC
LIMIT 100;
```

**SQLite**:
- With proper indexes: 10-50ms
- Full table scan: 100-500ms
- **Limitation**: Simpler query planner

**PostgreSQL**:
- With proper indexes: 5-20ms
- Full table scan: 50-200ms
- **Advantage**: Better query optimization, parallel execution

**Winner**: ✅ **PostgreSQL** (for complex joins)

### Conclusion on Performance
- **Single-user, simple queries**: SQLite wins (2-3x faster)
- **Multi-user, concurrent writes**: PostgreSQL wins (only option)
- **Complex analytical queries**: PostgreSQL slight edge
- **For RoboMage Scenario A/B**: SQLite is faster
- **For RoboMage Scenario C**: PostgreSQL is required

---

## 🛠️ Operational Considerations

### Deployment Complexity

**SQLite Deployment**:
```bash
# User perspective:
pixi install
python -m robomage.dashboard

# Under the hood:
# - Database created automatically on first run
# - Location: ~/.robomage/robomage.db
# - Migrations: Automatic on startup
# - Backups: cp ~/.robomage/robomage.db backup.db
```
**Effort**: 0 minutes  
**Expertise**: None required

**PostgreSQL Deployment**:
```bash
# System admin perspective:
# 1. Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# 2. Create database and user
sudo -u postgres createuser robomage_user
sudo -u postgres createdb robomage_db
sudo -u postgres psql
> GRANT ALL ON DATABASE robomage_db TO robomage_user;
> ALTER USER robomage_user WITH PASSWORD 'secure_password';

# 3. Configure pg_hba.conf for network access
sudo vim /etc/postgresql/14/main/pg_hba.conf

# 4. Set up connection pooling (pgbouncer)
# 5. Configure backups (pg_dump cron job)
# 6. Set up monitoring (prometheus + grafana)

# User perspective:
export DATABASE_URL=postgresql://robomage_user:password@db-server:5432/robomage_db
pixi install
python -m robomage.dashboard
```
**Effort**: 2-4 hours initial, ongoing maintenance  
**Expertise**: Database administration required

### Backup and Recovery

**SQLite**:
```bash
# Backup (online, safe with WAL):
sqlite3 robomage.db ".backup backup.db"

# Or simple copy:
cp ~/.robomage/robomage.db /backups/robomage-2025-11-25.db

# Restore:
cp /backups/robomage-2025-11-25.db ~/.robomage/robomage.db

# Git tracking (for small databases):
git add robomage.db
git commit -m "Session data checkpoint"
```
**User-friendly**: ✅ Yes, anyone can do this  
**Automated**: Easy with cron

**PostgreSQL**:
```bash
# Backup:
pg_dump -U robomage_user robomage_db > backup.sql

# Point-in-time recovery (requires WAL archiving setup):
# ... complex configuration ...

# Restore:
psql -U robomage_user robomage_db < backup.sql
```
**User-friendly**: ❌ Requires DB knowledge  
**Automated**: Requires proper setup

---

## 🔒 Security Considerations

### SQLite Security Model
- **File permissions only**: Unix file permissions protect database
- **No network exposure**: Can't be attacked over network
- **No authentication**: Anyone with file access has full access
- **Attack surface**: Minimal (just file system)

**For Scenario A/B**: ✅ Adequate
- User owns their database file
- Standard Unix permissions sufficient
- No network attack vector

**For Scenario C**: ❌ Inadequate
- Need role-based access control
- Need audit logging
- Need encryption in transit

### PostgreSQL Security Model
- **Role-based access**: Granular permissions (SELECT, INSERT, UPDATE, DELETE)
- **Row-level security**: User can only see their data
- **SSL/TLS**: Encrypted network connections
- **Audit logging**: Track who did what and when
- **Password policies**: Enforce strong passwords, rotation

**For Scenario C**: ✅ Required
- Must have proper multi-user security
- Compliance and audit requirements

---

## 🔄 Migration Path Analysis

### SQLite → PostgreSQL Migration Difficulty

**Schema Migration**:
```python
# SQLAlchemy makes this relatively easy:
# 1. Same models work with both databases
# 2. Change connection string:

# SQLite:
engine = create_engine("sqlite:///robomage.db")

# PostgreSQL:
engine = create_engine("postgresql://user:pass@host/db")
```

**Data Migration**:
```bash
# Option 1: Export/Import
sqlite3 robomage.db .dump > dump.sql
# Edit dump.sql (SQLite → PostgreSQL syntax differences)
psql robomage_db < dump.sql

# Option 2: Use migration tool
pgloader robomage.db postgresql://user:pass@host/db

# Option 3: Application-level migration
python migrate_data.py --from sqlite:///robomage.db \
                       --to postgresql://user:pass@host/db
```

**Effort**: 1-2 days for migration script + testing  
**Risk**: Medium (data transformation issues, downtime)

**Key Point**: If you use **SQLAlchemy** from the start, migration is easier.  
If you use **raw SQLite-specific SQL**, migration is painful.

### PostgreSQL → SQLite Migration (Downgrade)

**Why you'd want this**:
- Facility service didn't work out
- Need offline capability
- Simplify operations

**Difficulty**: Easier than upgrade
- PostgreSQL has more features
- Just export data, import to SQLite
- Might lose some constraints/triggers

**Verdict**: Migration in either direction is feasible with proper abstraction.

---

## 💰 Cost Analysis

### Total Cost of Ownership (1 Year)

**SQLite**:
- **Development**: 3 days (simple implementation)
- **Deployment**: 0 hours (automatic)
- **Maintenance**: 0 hours (self-managing)
- **Infrastructure**: $0 (no server needed)
- **Training**: 0 hours (invisible to users)
- **Total**: ~$3,000 (dev time only @ $1k/day)

**PostgreSQL**:
- **Development**: 5 days (connection pooling, auth, etc.)
- **Deployment**: 8 hours (initial setup)
- **Maintenance**: 2 hours/month (backups, monitoring, updates)
- **Infrastructure**: $100-500/month (server/cloud)
- **Training**: 4 hours (DBA concepts for team)
- **Total**: ~$11,000 (dev + ops @ $1k/day, infra @ $200/mo)

**Cost Difference**: PostgreSQL is **3-4x more expensive**

**When PostgreSQL is worth it**:
- Multi-user requirements (required)
- High availability needs (99.9% uptime)
- Compliance requirements (audit trails)
- Scale (>100 concurrent users)

**When SQLite is better value**:
- Single-user or small team
- Local-first architecture
- Simple deployment requirement
- Limited operational resources

---

## 🎯 Recommendation Matrix

| Scenario | Timeline | Users | Concurrent Access | Recommendation | Confidence |
|----------|----------|-------|-------------------|----------------|------------|
| **Individual Scientist** | Now | 1 | Single-user | ✅ **SQLite** | Very High |
| **Shared Workstation** | Now | 1-3 | Sequential | ✅ **SQLite** (per-user DB) | High |
| **Small Team** | 6 months | 5-10 | Low concurrency | ✅ **SQLite** (with monitoring) | Medium |
| **Facility Service** | 1+ year | 50+ | High concurrency | ✅ **PostgreSQL** | Very High |

---

## 🚀 Strategic Recommendation

### Phase 1: Start with SQLite (NOW)
**Rationale**:
1. Matches current localhost architecture perfectly
2. Zero operational overhead for scientists
3. Faster development (3 days vs 5 days)
4. Lower risk (simpler = fewer bugs)
5. Better performance for single-user workloads
6. Can ship to users faster

**Critical Success Factors**:
- ✅ Use **SQLAlchemy** for abstraction (enables future migration)
- ✅ Design schema for multi-user (add user_id columns even if unused)
- ✅ **Investigate NFS usage** at NSLS-II (potential blocker)
- ✅ Document migration path to PostgreSQL
- ✅ Monitor for concurrency issues (measure, don't guess)

### Phase 2: Monitor and Measure (Months 1-6)
**Metrics to Track**:
1. **Concurrent access patterns**: How often do users run multiple tools?
2. **Database growth**: How large do databases get?
3. **Query performance**: Any slow queries emerging?
4. **User feedback**: Do they need collaboration features?

**Decision Criteria for PostgreSQL Migration**:
- 📊 More than 3 concurrent users per database regularly
- 📊 Users requesting shared sessions / collaboration
- 📊 Queries consistently >100ms
- 📊 Facility wants centralized service

### Phase 3: Migrate if Needed (Year 1+)
**If metrics show need**:
1. Deploy PostgreSQL alongside SQLite
2. Add `--database-url` configuration option
3. Migrate power users first (beta test)
4. Keep SQLite as option for offline/single-user use

**If metrics show SQLite is fine**:
1. Keep using SQLite
2. Add features (caching, reporting) on solid foundation
3. Avoid complexity that isn't needed

---

## ⚠️ Critical Risks and Mitigations

### Risk 1: NFS File Locking (HIGH PRIORITY)

**Risk**: If NSLS-II users store `~/.robomage/` on NFS, database corruption likely.

**Investigation Required**:
```bash
# Check if home directory is on NFS:
df -T ~

# Output:
# nfs4  → ⚠️ HIGH RISK (SQLite not safe on NFS)
# ext4  → ✅ SAFE (local filesystem)
```

**Mitigations**:
1. **Best**: Detect NFS and warn user, suggest local path
   ```python
   if is_nfs_mount(db_path):
       warnings.warn(
           "Database on NFS detected. This can cause corruption. "
           "Please set ROBOMAGE_DB_PATH to local directory."
       )
   ```

2. **Good**: Default to `/tmp/robomage-{username}/` on NFS systems
3. **Acceptable**: Document the limitation clearly

**Action**: Check with NSLS-II IT about typical storage patterns **BEFORE implementing**.

### Risk 2: Concurrent Write Conflicts

**Risk**: Dashboard + CLI batch job writing simultaneously causes lock timeout.

**Mitigation**:
1. **Enable WAL mode** (allows concurrent read while writing)
   ```python
   PRAGMA journal_mode=WAL;
   PRAGMA busy_timeout=5000;  # Wait 5 seconds instead of failing
   ```

2. **Implement retry logic** on SQLITE_BUSY errors
3. **Monitor for conflicts** and alert if frequent

**Fallback**: If conflicts are common, trigger PostgreSQL migration.

### Risk 3: Database File Size

**Risk**: Peaks table grows large (500k+ rows), performance degrades.

**Mitigation**:
1. **Proper indexing** on common query columns
2. **VACUUM regularly** to reclaim space
3. **Benchmark** with realistic data (use NSLS-II actual datasets)
4. **Archive old sessions** (move to separate .db files)

**Threshold**: If database >1GB, re-evaluate PostgreSQL.

---

## 📝 Decision Record

### Recommended Decision

**Choose SQLite for Sprint 5 implementation** with these requirements:

**Must Have**:
1. ✅ Use SQLAlchemy ORM (enables future PostgreSQL migration)
2. ✅ Design schema with user_id columns (even if unused)
3. ✅ Enable WAL mode for better concurrency
4. ✅ Implement NFS detection and warning
5. ✅ Add `ROBOMAGE_DB_PATH` environment variable for custom location

**Should Have**:
6. ✅ Document PostgreSQL migration path
7. ✅ Add database metrics/monitoring hooks
8. ✅ Implement connection pooling pattern (even for SQLite)

**Could Have**:
9. 🔄 Support both SQLite and PostgreSQL via configuration
10. 🔄 Auto-migration tool (SQLite → PostgreSQL)

**Won't Have (Now)**:
11. ❌ Multi-user authentication
12. ❌ Network database access
13. ❌ Replication/high availability

### Validation Criteria

**Decision is correct if**:
- ✅ 95%+ of users are single-user local workflows
- ✅ Database files stay under 1GB
- ✅ No NFS corruption issues (mitigated)
- ✅ Concurrent write conflicts <1% of operations

**Trigger PostgreSQL migration if**:
- ❌ >10% of users request collaboration features
- ❌ Concurrent write conflicts >5% of operations
- ❌ Facility decides to deploy centralized service
- ❌ Database size >2GB regularly

### Timeline

- **Sprint 5 (Now)**: Implement with SQLite
- **Month 3**: Review metrics and user feedback
- **Month 6**: Decision point for PostgreSQL migration
- **Year 1**: Potential PostgreSQL deployment for facility service

---

## 🔗 References

- [SQLite When to Use](https://www.sqlite.org/whentouse.html)
- [SQLite on NFS](https://www.sqlite.org/draft/useovernet.html) - **Official warning**
- [PostgreSQL vs SQLite](https://www.sqlite.org/draft/whentouse.html#dbchoices)
- [SQLite Performance Tuning](https://www.sqlite.org/pragma.html)
- [SQLAlchemy Database Abstraction](https://docs.sqlalchemy.org/en/20/)

---

## ✅ Final Answer

**Start with SQLite. Monitor. Migrate if needed.**

**Why this is the right choice**:
1. ✅ Matches RoboMage's localhost architecture
2. ✅ Faster to implement (get to users sooner)
3. ✅ Better performance for single-user (most users)
4. ✅ Zero operational overhead (scientists, not DBAs)
5. ✅ Easy migration path with SQLAlchemy
6. ✅ Can always upgrade, hard to downgrade

**The only way SQLite is wrong**:
- NFS storage at NSLS-II (needs investigation)
- Immediate need for multi-user (not the case)
- Already have PostgreSQL infrastructure (don't think so)

**Next Step**: Confirm storage patterns at NSLS-II, then implement SQLite-based persistence.
