# 🚀 Quick Start: Week 2 Implementation

**Copy and paste this into your next chat to begin Week 2 work:**

---

## Chat Starter Message

```
Hi! I'm ready to implement Week 2 of the RoboMage inspection tools.

Context:
- Week 1 complete: All tests passing (233/233), warnings fixed, docs updated
- Starting: Week 2 Day 1 - Node I/O Inspector data capture layer
- Full plan: docs/NEXT-STEPS-WEEK-2.md (daily breakdown with code examples)
- Architecture: docs/inspection-tools-design.md (5 tools, 4-5 week timeline)

Goal for Day 1:
Add inspection hooks to WorkflowOrchestrator to capture node inputs/outputs during execution.

Tasks:
1. Extend WorkflowOrchestrator with enable_inspection parameter
2. Create inspection data models (NodeIOSnapshot)
3. Add _serialize_for_inspection() method
4. Add capture hooks in _execute_node()
5. Write comprehensive unit tests

Let's begin with Task 1: Reviewing the current WorkflowOrchestrator and planning the changes.
```

---

## Files to Have Open

1. **`docs/NEXT-STEPS-WEEK-2.md`** - Your daily guide
2. **`docs/inspection-tools-design.md`** - Complete architecture
3. **`src/robomage/orchestrator.py`** - File you'll be modifying
4. **`src/robomage/data/models.py`** - Reference for data structures

---

## Context to Attach (if needed)

Point the assistant to:
- Current project status: "233/233 tests passing, Sprint 8 complete"
- Implementation plan: `docs/NEXT-STEPS-WEEK-2.md` 
- Architecture: `docs/inspection-tools-design.md`
- Current code: `src/robomage/orchestrator.py`

---

## Expected Flow

### Day 1 Session
1. **Review** existing orchestrator code
2. **Design** inspection hook integration points
3. **Create** `src/robomage/inspection/models.py`
4. **Modify** `src/robomage/orchestrator.py`
5. **Write** `tests/test_node_inspector.py`
6. **Verify** tests pass and no performance impact

### Day 2 Session
Start with: "Week 2 Day 1 complete. Moving to Day 2: Database storage for inspection data."

### Day 3 Session
Start with: "Week 2 Day 2 complete. Moving to Day 3: Dashboard UI for inspector."

---

## Success Indicators

After each day, you should have:
- ✅ All existing tests still pass (233+)
- ✅ New tests added for day's work
- ✅ Code passes all quality checks (`pixi run check`)
- ✅ Documentation updated
- ✅ Ready for next day's tasks

---

## Quick Commands Reference

```bash
# Verify starting state
pixi run test                    # Should show 233 passed, ~10 warnings

# During development
pixi run pytest tests/test_node_inspector.py -v    # Run new tests
pixi run check                                      # Run all quality checks

# Test performance
pixi run pytest tests/test_node_inspector.py -v -k "performance"

# Start services (for dashboard testing later)
pixi run start-all
```

---

## Files You'll Create This Week

### Day 1
- `src/robomage/inspection/__init__.py`
- `src/robomage/inspection/models.py`
- `tests/test_node_inspector.py`

### Day 2
- `tests/test_node_inspection_persistence.py`

### Day 3
- `src/robomage/dashboard/layouts/inspector_layout.py`
- `src/robomage/dashboard/components/node_inspector_panel.py`
- `src/robomage/dashboard/callbacks/inspector.py`
- `tests/test_dashboard_inspector.py`

### Day 5
- `src/robomage/dashboard/layouts/analysis_viewer_layout.py`

---

## If You Get Stuck

1. **Check the plan**: `docs/NEXT-STEPS-WEEK-2.md` has detailed examples
2. **Check architecture**: `docs/inspection-tools-design.md` has complete design
3. **Check patterns**: Look at similar code (workflow_layout.py, orchestrator.py)
4. **Check troubleshooting**: `docs/TROUBLESHOOTING.md` has solutions
5. **Ask for help**: Describe what you're trying to do and where you're stuck

---

## Key Design Decisions

### Inspection Should Be:
- ✅ **Toggle-able** - Enable/disable via parameter
- ✅ **Non-invasive** - No impact on workflow execution
- ✅ **Efficient** - <5% overhead when enabled, 0% when disabled
- ✅ **Persistent** - Store in database for later review
- ✅ **Flexible** - Easy to extend for new data types

### Inspection Should NOT:
- ❌ Store full data arrays (use summaries/samples)
- ❌ Block workflow execution
- ❌ Be enabled by default
- ❌ Break existing functionality
- ❌ Impact production workflows

---

## Documentation Updates Needed

As you complete each day, update:
1. **This file** - Mark tasks complete with checkboxes
2. **README.md** - Add Inspector feature to features list
3. **Architecture docs** - Document any design decisions
4. **Code docstrings** - Add examples and usage notes

---

## End of Week Deliverables

By Friday (Day 5), you should have:
- ✅ Node I/O Inspector fully functional
- ✅ Inspector tab in dashboard
- ✅ Data visualizations working
- ✅ Export functionality
- ✅ Analysis viewer foundation ready
- ✅ 20+ new tests passing
- ✅ Documentation complete

---

**Ready? Copy the "Chat Starter Message" above and paste it into your next chat session!** 🚀

---

**Quick Links:**
- Full Plan: `docs/NEXT-STEPS-WEEK-2.md`
- Architecture: `docs/inspection-tools-design.md`
- Week 1 Summary: `docs/WEEK-1-COMPLETION.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`

**Last Updated**: December 1, 2025  
**Status**: Ready to Begin Week 2
