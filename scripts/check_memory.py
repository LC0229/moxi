#!/usr/bin/env python3
"""Quick memory check script."""

import subprocess
import sys

def get_memory_usage():
    """Get memory usage for all processes."""
    try:
        # Get top memory consumers
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        processes = []
        for line in result.stdout.split("\n")[1:]:  # Skip header
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 11:
                pid = parts[1]
                mem_percent = parts[3]
                command = " ".join(parts[10:])
                processes.append((float(mem_percent), pid, command))
        
        # Sort by memory
        processes.sort(reverse=True)
        
        print("=== Top 15 Memory Consumers ===\n")
        for mem, pid, cmd in processes[:15]:
            print(f"PID: {pid:8s}  Memory: {mem:6.2f}%  {cmd[:60]}")
        
        # Check Cursor specifically
        print("\n=== Cursor Processes ===\n")
        cursor_procs = [p for p in processes if "cursor" in p[2].lower()]
        total_cursor_mem = sum(p[0] for p in cursor_procs)
        for mem, pid, cmd in cursor_procs[:10]:
            print(f"PID: {pid:8s}  Memory: {mem:6.2f}%  {cmd[:60]}")
        if cursor_procs:
            print(f"\nTotal Cursor Memory: {total_cursor_mem:.2f}%")
        
        # Check Python processes
        print("\n=== Python/Training Processes ===\n")
        python_procs = [p for p in processes if "python" in p[2].lower() or "training" in p[2].lower()]
        total_python_mem = sum(p[0] for p in python_procs)
        for mem, pid, cmd in python_procs[:10]:
            print(f"PID: {pid:8s}  Memory: {mem:6.2f}%  {cmd[:60]}")
        if python_procs:
            print(f"\nTotal Python/Training Memory: {total_python_mem:.2f}%")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    get_memory_usage()

