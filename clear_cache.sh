#!/bin/bash
# Clear Python bytecode cache
# Run this if you encounter import errors or stale code issues

echo "🧹 Clearing Python bytecode cache..."

# Clear __pycache__ directories
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Clear .pyc files  
find . -name "*.pyc" -delete 2>/dev/null || true

# Clear .pyo files (optimized bytecode)
find . -name "*.pyo" -delete 2>/dev/null || true

echo "✅ Cache cleared successfully!"
echo ""
echo "If you're still having issues, try:"
echo "  1. pixi clean"
echo "  2. pixi install"
