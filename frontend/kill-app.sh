#!/bin/bash

# BotArmy Frontend Kill Script (Shell version)

echo "🔪 Killing BotArmy processes..."

# Kill Next.js processes on port 3000
echo "  - Killing Next.js processes on port 3000..."
lsof -ti:3000 | xargs kill -9 2>/dev/null && echo "    ✅ Next.js processes killed" || echo "    No processes found on port 3000"

# Kill any remaining Next.js processes
echo "  - Killing Next.js server processes..."
pkill -f "next-server" 2>/dev/null && echo "    ✅ Next.js server processes killed" || echo "    No next-server processes found"

# Call backend kill script if it exists
BACKEND_KILL_SCRIPT="../backend/scripts/kill_processes.sh"
if [ -f "$BACKEND_KILL_SCRIPT" ]; then
    echo ""
    echo "  - Calling backend kill script..."
    bash "$BACKEND_KILL_SCRIPT"
else
    echo "    ⚠️  Backend kill script not found at $BACKEND_KILL_SCRIPT"
fi

echo ""
echo "🎯 Frontend and backend cleanup complete!"
echo "   You can now run: npm run dev"