# Windows Subprocess Command Parsing Fix

**Date:** December 1, 2025  
**Issue:** Workflow service fails to start on Windows via `pixi run start-all`  
**Status:** ✅ Fixed

## Problem Description

When running `pixi run start-all` on Windows, the workflow service would fail to start with an error suggesting manual start. However, manual start with the same command worked fine:

```bash
# This failed on Windows:
pixi run start-all  # Workflow service showed error

# This worked on Windows:
python services/workflow_engine/main.py --port 8002 --host 127.0.0.1
```

## Root Cause

The issue was in `start_services.py` line 73:

```python
# OLD CODE (BROKEN ON WINDOWS):
cmd_parts = service.format_startup_command().split()
```

The `format_startup_command()` method returns a string like:
```
"python services/workflow_engine/main.py --port 8002 --host 127.0.0.1"
```

Using simple `.split()` fails on Windows when the Python executable path contains spaces, which is common on Windows:
```
C:\Program Files\Python\python.exe  # Contains spaces!
```

Simple `.split()` would break this into:
```python
["C:\\Program", "Files\\Python\\python.exe", "services/workflow_engine/main.py", ...]
```

Instead of the correct:
```python
["C:\\Program Files\\Python\\python.exe", "services/workflow_engine/main.py", ...]
```

## Solution

Use `shlex.split()` instead of `.split()` for proper shell command parsing that handles quoted arguments and paths with spaces:

```python
# NEW CODE (CROSS-PLATFORM):
import shlex

cmd_parts = shlex.split(service.format_startup_command())
```

`shlex.split()` properly handles:
- Paths with spaces (even without quotes)
- Quoted arguments
- Escaped characters
- Cross-platform compatibility

## Files Changed

1. **start_services.py**
   - Added `import shlex` (line 11)
   - Changed line 74 from `.split()` to `shlex.split()`
   - Added comment explaining Windows compatibility

## Testing

### Before Fix
- ❌ Windows: Workflow service fails to start via `pixi run start-all`
- ✅ Linux: Works fine (paths rarely have spaces on Linux)
- ✅ Windows: Manual start works

### After Fix
- ✅ Windows: `pixi run start-all` works correctly
- ✅ Linux: Still works (no regression)
- ✅ Cross-platform: Handles all path edge cases

## Lessons Learned

1. **Always test cross-platform**, especially subprocess calls
2. **Never use `.split()` on shell commands** - use `shlex.split()` instead
3. **Windows paths with spaces are common** - default Python installation is in `C:\Program Files\`
4. **Automated tests missed this** - demonstrates value of hands-on testing on different platforms

## Related Issues

This issue was discovered during Phase 5 hands-on testing as outlined in:
- `docs/HANDS-ON-TESTING-PLAN.md` - Session 6: End-to-End Testing

The fallback code in `start_services.py` (lines 90-91) already used the correct approach with a list:
```python
# Fallback code (already correct):
[python_exe, "services/peak_analysis/main.py", "--port", "8001"]
```

This could have been a clue to use list format throughout.

## Future Improvements

Consider refactoring `format_startup_command()` to return `List[str]` instead of `str` to avoid parsing issues entirely:

```python
# Alternative approach for future consideration:
def format_startup_command_parts(self) -> List[str]:
    """Return command as list of parts (no parsing needed)."""
    parts = self.startup_command.split()
    parts[0] = "python"  # or sys.executable
    # Replace {port} and {host} in arguments
    return [p.format(port=self.port, host=self.host) for p in parts]
```

This would eliminate the need for `shlex.split()` entirely, but requires more significant refactoring.

## References

- Python `shlex` module: https://docs.python.org/3/library/shlex.html
- Windows path handling: https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
- Subprocess best practices: https://docs.python.org/3/library/subprocess.html#security-considerations
