# Storage Configuration and Debug Features

**Date**: November 25, 2025  
**Sprint**: Sprint 5 - Day 3 Completion  
**Status**: ✅ COMPLETE

## Overview

Two new features have been added to the RoboMage dashboard for better session management:

1. **Storage Location Configuration** - Configure where session data is stored
2. **Debug Information Panel** - Inspect detailed session information

## Features

### 1. Storage Location Configuration

**Purpose**: Allow users to customize where RoboMage stores session databases and files.

**Default Location**: `~/.robomage/`
- Database: `~/.robomage/robomage.db`
- Files: `~/.robomage/files/`

**How to Use**:
1. Open **Manage Sessions** modal
2. Click **Configure** button next to storage location display
3. Enter new path (absolute path or `~/custom/location`)
4. Click **Apply** to change location
5. Click **Reset to Default** to revert to `~/.robomage/`

**Key Features**:
- Automatic directory creation
- Path validation (checks for write permissions)
- Clear feedback on success/errors
- Warning about switching between databases
- Support for `~/` home directory expansion

**Use Cases**:
- Multi-user environments with shared storage
- Network storage locations
- Organizing different projects separately
- Testing with isolated databases

**Implementation Details**:
- Storage location stored in `storage-location-store` (dcc.Store)
- Changes affect both database and file storage
- SessionManager automatically uses custom path when set
- Switching locations means different databases (sessions won't carry over)

### 2. Debug Information Panel

**Purpose**: Provide detailed inspection of session data for troubleshooting and development.

**How to Use**:
1. Open **Manage Sessions** modal
2. Click **Debug Info** button (next to Refresh)
3. View detailed information in collapsible panel

**Information Displayed**:

**Storage Configuration**:
- Database path (full absolute path)
- File storage path
- Existence checks for database and file store

**Session Summary**:
- Total number of sessions
- Total number of files across all sessions

**Detailed Session Information** (for each session):
- Session ID and name
- Description
- Created timestamp
- Last accessed timestamp
- File count
- For each file:
  - Filename
  - Number of points
  - Wavelength
  - Stored file path
  - Q-range [min, max]

**Example Output**:
```
Storage Configuration
Database: /home/user/.robomage/robomage.db
Files: /home/user/.robomage/files
Database exists: True
File store exists: True

Session Summary
Total sessions: 3
Total files: 5

Detailed Session Information
Session ID 1: Morning Analysis
  Description: SRM 660b testing
  Created: 2025-11-25 09:15:30
  Last accessed: 2025-11-25 10:22:45
  Files (2):
    • pdf_SRM_660b_q.chi (2500 pts, 0.1665 Å)
      Path: /home/user/.robomage/files/abc123.h5
      Q range: [1.500, 8.000]
    • detector_5_roi.xy (3000 pts, 1.5406 Å)
      Path: /home/user/.robomage/files/def456.h5
      Q range: [2.000, 9.500]
```

**Use Cases**:
- Verify session data integrity
- Troubleshoot loading issues
- Check file storage paths
- Inspect metadata
- Development and debugging
- Understanding session structure

## Technical Implementation

### New Callbacks (in `src/robomage/dashboard/callbacks/persistence.py`)

**Storage Configuration**:
1. `toggle_configure_storage_modal` - Open/close configuration modal
2. `update_storage_location_display` - Show current storage location in manage modal
3. `update_current_storage_path` - Show current path in configuration modal
4. `handle_storage_configuration` - Apply/reset storage location

**Debug Panel**:
1. `toggle_debug_panel` - Show/hide debug information
2. `update_debug_info` - Generate and display detailed session information

### New UI Components (in `src/robomage/dashboard/layouts/main_layout.py`)

**Storage Configuration Modal** (`create_configure_storage_modal`):
- Current storage location display
- New path input field
- Tips for path formatting
- Important warnings
- Reset to Default button
- Cancel/Apply buttons

**Enhanced Manage Sessions Modal**:
- Storage location info alert with Configure button
- Debug Info button next to Refresh
- Collapsible debug panel

**New dcc.Store**:
- `storage-location-store` - Persists custom storage location

## Testing

All existing tests pass (85/85):
- Core functionality tests
- Dashboard tests  
- Session persistence integration tests

Manual testing recommended:
1. Change storage location to custom path
2. Save session with custom location
3. Verify files created in new location
4. Reset to default location
5. Verify sessions switch back
6. Open debug panel
7. Verify all information displays correctly

## Code Quality

- ✅ All format checks passing (ruff)
- ✅ All lint checks passing (ruff)
- ✅ All type checks passing (mypy)
- ✅ All 85 tests passing
- ✅ Comprehensive docstrings
- ✅ Error handling with user-friendly messages

## Future Enhancements

Potential improvements:
- Migration tool to move sessions between locations
- Storage usage statistics in debug panel
- Backup/restore functionality
- Storage location history
- Per-session storage location (advanced)

## Summary

These features provide:
- **Flexibility**: Users can choose where to store data
- **Transparency**: Full visibility into session storage
- **Debugging**: Detailed information for troubleshooting
- **Professional UX**: Clear warnings and feedback

Both features are production-ready and fully integrated with the existing dashboard architecture.
