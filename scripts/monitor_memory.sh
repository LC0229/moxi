#!/bin/bash
# Memory monitoring script for Mac

echo "=== Memory Usage Monitor ==="
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "=== $(date) ==="
    echo ""
    
    # Total memory
    echo "--- System Memory ---"
    vm_stat | head -5
    echo ""
    
    # Top memory consumers
    echo "--- Top 10 Memory Consumers ---"
    ps aux | awk '{print $2, $4, $11}' | sort -nrk 2 | head -10 | \
        awk '{printf "PID: %-8s Memory: %-6s%% %s\n", $1, $2, $3}'
    echo ""
    
    # Cursor processes
    echo "--- Cursor Processes ---"
    ps aux | grep -i cursor | grep -v grep | awk '{printf "PID: %-8s Memory: %-6s%% %s\n", $2, $4, $11}'
    echo ""
    
    # Python processes (training)
    echo "--- Python/Training Processes ---"
    ps aux | grep -E "(python|training)" | grep -v grep | awk '{printf "PID: %-8s Memory: %-6s%% %s\n", $2, $4, $11}'
    echo ""
    
    sleep 2
done

