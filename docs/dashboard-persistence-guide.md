# RoboMage Dashboard: Session Persistence Guide

**Version**: 1.0  
**Date**: November 25, 2025  
**For**: RoboMage Dashboard Users

## Quick Start

The RoboMage Dashboard can save your analysis sessions so you can close the browser and resume later with all files and settings intact.

### TL;DR
1. Upload files → Click **"Save Session"** → Enter name → Saved! ✅
2. Later: Click **"Load Session"** → Select session → Click **"Load"** → Restored! ✅

---

## Overview

### What Gets Saved?
When you save a session, the dashboard preserves:
- ✅ All uploaded diffraction files (.chi and .xy)
- ✅ Q-spacing and intensity arrays (complete datasets)
- ✅ Per-file wavelength settings
- ✅ File metadata and comments

### What Doesn't Get Saved? (Future Enhancements)
- ❌ Plot settings (zoom level, axis selection)
- ❌ Peak analysis results
- ❌ Active tab selection

---

## Session Management Features

### 📁 Save Session

**Purpose**: Save your current work for later

**How to Use**:
1. Upload one or more files in the **Data Import** tab
2. Set wavelengths for each file (or use default 0.1665 Å)
3. Click the **"Save Session"** button (green, in header)
4. Enter a **session name** (required) - Example: "November 2025 SRM Calibration"
5. Optionally add a **description** - Example: "SRM 660b with 0.1665 Å wavelength"
6. Click **"Save"**

**Success Indicators**:
- ✅ Green alert: "Session 'Your Name' saved successfully with X files!"
- Session appears in Load and Manage lists
- Files stored in `~/.robomage/files/session_X/`

**Possible Errors**:
| Error | Cause | Solution |
|-------|-------|----------|
| "Please enter a session name" | Empty name field | Type a descriptive name |
| "No files to save" | No files uploaded | Upload files first |
| "Session name already exists" | Duplicate name | Choose a different name |

---

### 📂 Load Session

**Purpose**: Restore a previously saved session

**How to Use**:
1. Click the **"Load Session"** button (blue, in header)
2. Review the session table:
   - **Name**: Session identifier
   - **Description**: Optional notes
   - **Files**: Number of files in session
   - **Created**: Date/time saved
3. Click **"Load"** on the session you want
4. Wait for confirmation (green alert)

**Success Indicators**:
- ✅ Green alert: "Session 'Name' loaded successfully! Restored X files."
- Files appear in Data Import tab file list
- Wavelengths restored (check file info)
- Can immediately plot or analyze

**Possible Errors**:
| Error | Cause | Solution |
|-------|-------|----------|
| "Session not found!" | Deleted/corrupted session | Try a different session |
| "Session 'Name' has no files!" | Empty session | Delete and create new |
| "Unexpected error" | Database issue | Restart dashboard |

**Workflow Tips**:
- Load overwrites current files (any unsaved work lost!)
- Close the Load modal before working with files
- To compare sessions, load one, plot, then load another

---

### 🗂️ Manage Sessions

**Purpose**: View all sessions, delete old ones

**How to Use**:
1. Click the **"Manage Sessions"** button (teal, in header)
2. Review session cards showing:
   - Session name and description
   - File count
   - Creation date
3. Click **"Refresh"** to update the list
4. Click **"Delete"** to remove a session (⚠️ permanent!)

**Delete Warning**:
- ⚠️ Deletion is **immediate** - no undo!
- Removes both database entry and physical files
- Any loaded session remains in dashboard until overwritten

**Organizational Tips**:
- Use descriptive names: "2025-11-13 SRM Calibration" better than "Test1"
- Add descriptions for future reference
- Delete old test sessions periodically
- Refresh list if sessions don't appear

---

## Example Workflows

### Workflow 1: Daily Analysis Session

**Scenario**: Analyze samples daily, save for future reference

```
Day 1:
1. Upload sample_2025-11-25.chi
2. Set wavelength: 0.1665 Å
3. Visualize → Analyze peaks
4. Save Session: "2025-11-25 Daily Run"
5. Close browser ✅

Day 2:
1. Load Session: "2025-11-25 Daily Run"
2. Compare with new sample
3. Save new session: "2025-11-26 Daily Run"
```

---

### Workflow 2: Multi-File Comparison

**Scenario**: Compare 3 samples from different conditions

```
1. Upload:
   - sample_300K.chi (set wavelength 0.1665 Å)
   - sample_400K.chi (set wavelength 0.1665 Å)
   - sample_500K.chi (set wavelength 0.1665 Å)

2. Save Session: "Temperature Series Nov 2025"
   Description: "SRM samples at 300K, 400K, 500K"

3. Later: Load session → All 3 files ready to overlay
```

---

### Workflow 3: Long-Term Project

**Scenario**: Multi-month refinement project

```
Week 1: Initial data collection
- Save: "Project Alpha - Week 1"

Week 4: Additional measurements
- Load: "Project Alpha - Week 1" 
- Add new files
- Save: "Project Alpha - Week 4"

Week 12: Final analysis
- Load: "Project Alpha - Week 4"
- Peak analysis
- Save: "Project Alpha - Final"
```

---

## Troubleshooting

### Problem: Session won't save

**Symptoms**: Error message after clicking Save

**Checklist**:
1. ✅ Did you upload files? (Check Data Import tab)
2. ✅ Did you enter a session name? (Required field)
3. ✅ Is the name unique? (Duplicates not allowed)
4. ✅ Do you have disk space? (Check `~/.robomage/`)

**Still not working?**
- Restart the dashboard: `python -m robomage.dashboard`
- Check terminal for error messages
- Verify `~/.robomage/` directory exists and is writable

---

### Problem: Loaded session missing files

**Symptoms**: Load succeeds but files don't appear

**Possible Causes**:
1. **Session had no files** - Check file count in session list
2. **Database corruption** - Delete and recreate session
3. **File permissions** - Check `~/.robomage/files/` is readable

**Debug Steps**:
1. Click Manage Sessions → Check file count
2. If count is 0, session is empty (delete it)
3. If count > 0 but files missing, try different session
4. If all sessions fail, restart dashboard

---

### Problem: "Session already exists" error

**Cause**: Trying to save with a name that's already used

**Solutions**:
1. **Rename**: Add date/version - "Analysis v2" instead of "Analysis"
2. **Delete old**: Manage Sessions → Delete old version → Save again
3. **Load and modify**: Load old session → Modify → Save with new name

---

### Problem: Dashboard performance slow after loading

**Cause**: Large files (50k+ data points) or many files (10+)

**Solutions**:
1. **Reduce files**: Save separate sessions for each sample
2. **Trim data**: Use Q-range trimming before saving
3. **Close/reopen**: Restart dashboard to clear memory

---

## Advanced Tips

### Organizing Sessions

**Use Naming Conventions**:
```
✅ Good: "2025-11-25-SRM660b-Calibration"
❌ Bad: "test1"

✅ Good: "ProjectAlpha-Sample03-HighTemp"
❌ Bad: "data"
```

**Use Descriptions**:
```
✅ Good: "SRM 660b calibration standard, λ=0.1665Å, 300K, beamline 28-ID-2"
❌ Bad: (empty)
```

### Session Lifecycle

**Best Practices**:
1. **Save often**: After each significant analysis step
2. **Version sessions**: "Analysis v1", "Analysis v2", etc.
3. **Clean up**: Delete test sessions weekly
4. **Export important data**: Copy files from `~/.robomage/files/` for backup

### Storage Management

**Default Location**: `~/.robomage/`

**Typical Sizes**:
- Database: <1 MB for 100 sessions
- Per file: 100-500 KB (5000 data points)
- 10 sessions × 3 files each: ~10-15 MB total

**To Clear All Data**:
```bash
# ⚠️ WARNING: Deletes all sessions permanently!
rm -rf ~/.robomage/
# Restart dashboard to recreate directory
```

**To Backup Sessions**:
```bash
# Copy entire persistence directory
cp -r ~/.robomage/ ~/backups/robomage-backup-2025-11-25/
```

---

## Integration with Analysis Workflow

### Before Persistence (Old Workflow)

```
1. Upload files
2. Analyze peaks
3. Take screenshots
4. Close browser → ❌ All work lost!
5. Next day: Re-upload everything
```

### With Persistence (New Workflow)

```
1. Upload files
2. Analyze peaks
3. Save Session
4. Close browser → ✅ Work preserved!
5. Next day: Load Session → Continue immediately
```

### Peak Analysis Integration

**Current State**: Sessions save files but not peak results

**Workaround**: After loading session, re-run peak analysis
- Settings preserved in Analysis tab
- Takes 1-2 seconds to recompute

**Future Enhancement** (Sprint 6): Save analysis results with session

---

## Keyboard Shortcuts

*Currently none - all actions via mouse clicks*

**Requested Features** (for future):
- `Ctrl+S`: Quick save current session
- `Ctrl+O`: Open load session dialog
- `Ctrl+Shift+S`: Save as new session

---

## Technical Details

### File Storage Format

**Database**: SQLite (`~/.robomage/robomage.db`)
- Schema: Sessions table, Files table (linked by session_id)
- Metadata: Names, descriptions, timestamps, wavelengths

**File Storage**: HDF5 format (`~/.robomage/files/session_X/*.h5`)
- Arrays: Q values, intensity values
- Metadata: Original filename, wavelength, comments

**Why HDF5?**
- Efficient binary storage (smaller than text)
- Preserves NumPy array precision
- Fast read/write operations
- Standard scientific data format

### Concurrency Support

**Multi-Window Safe**: Yes
- SQLite WAL mode enables concurrent reads
- Multiple dashboard instances can load same session
- Only one should write (save) at a time

### Data Integrity

**Validation**:
- Pydantic models validate data on load
- Q-values checked for sorting
- NaN/Inf values rejected
- Wavelength range checked (0.1-10 Å reasonable)

**Roundtrip Testing**:
```python
# Save → Load → Compare
original_data = ...
mgr.add_file(session_id, original_data)
loaded_data = mgr.file_store.read_file(file_id)
assert np.allclose(original_data.q, loaded_data.q)  # ✅ Passes
```

---

## FAQ

**Q: Can I save sessions with different file types mixed?**  
A: Yes! Mix .chi and .xy files in one session.

**Q: What happens if I save a session with the same name?**  
A: Error! Session names must be unique. Rename or delete old one.

**Q: Can I share sessions with collaborators?**  
A: Currently no built-in export. Manual: copy `~/.robomage/` directory.  
Future: Export as ZIP feature planned (Sprint 6).

**Q: Are sessions backed up automatically?**  
A: No. Manual backup recommended: `cp -r ~/.robomage/ ~/backup/`

**Q: Can I edit a session after saving?**  
A: No direct editing. Workflow: Load → Modify → Save with new name.

**Q: How many sessions can I have?**  
A: No hard limit. Tested with 100+. Performance may degrade beyond 500.

**Q: Can I save peak analysis results?**  
A: Not yet. Planned for Sprint 6.

**Q: What if my session is corrupted?**  
A: Delete it via Manage Sessions and recreate. Data in original files is safe.

---

## Getting Help

**If sessions won't save/load**:
1. Check terminal output for error messages
2. Verify `~/.robomage/` directory exists
3. Try restarting dashboard
4. Review this guide's Troubleshooting section

**For bugs or feature requests**:
- GitHub Issues: https://github.com/DanOlds/RoboMage/issues
- Include: Dashboard version, error message, steps to reproduce

**For questions**:
- Check `docs/persistence-layer-documentation.md` for API details
- Check `docs/persistence-quick-reference.md` for code examples

---

## Changelog

**Version 1.0** (November 25, 2025)
- Initial dashboard persistence release
- Save/Load/Manage session features
- File and wavelength preservation
- SQLite + HDF5 storage backend

**Planned for Version 1.1** (Sprint 6)
- Analysis results persistence
- Session export/import (ZIP format)
- Delete confirmation dialog
- Auto-save every 5 minutes

---

**End of Guide** - Happy analyzing! 🔬
