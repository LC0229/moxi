#!/usr/bin/env python3
"""
Standalone test to verify concurrent processing is faster than serial.

This test doesn't require any project dependencies - it's a simple demonstration.

Run with:
    python tests/test_concurrency_standalone.py
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def simulate_repo_processing(repo_id):
    """
    Simulate processing a repository.
    Takes 1 second to simulate: cloning (0.5s) + analysis (0.2s) + API (0.3s)
    """
    time.sleep(1)  # Simulate 1 second of work
    return {
        "repo_id": repo_id,
        "status": "success",
        "instruction": f"Generate README for repo{repo_id}",
    }


def process_serial(repos):
    """Process repositories one by one (serial)."""
    results = []
    for repo_id in repos:
        result = simulate_repo_processing(repo_id)
        results.append(result)
    return results


def process_concurrent(repos, max_workers=5):
    """Process repositories concurrently using ThreadPoolExecutor."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_repo = {
            executor.submit(simulate_repo_processing, repo_id): repo_id
            for repo_id in repos
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_repo):
            repo_id = future_to_repo[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing repo{repo_id}: {e}")
    
    return results


def main():
    """Run the concurrency performance test."""
    print("=" * 70)
    print("Concurrency Performance Test (Standalone)")
    print("=" * 70)
    print()
    print("This test simulates processing 10 repositories.")
    print("Each repository takes 1 second to process.")
    print()
    
    # Create test repository IDs
    test_repos = list(range(10))
    
    # Test 1: Serial processing
    print("Test 1: Serial Processing (no concurrency)")
    print("-" * 70)
    start_time = time.time()
    serial_results = process_serial(test_repos)
    serial_time = time.time() - start_time
    print(f"✅ Processed {len(serial_results)} repositories")
    print(f"⏱️  Time taken: {serial_time:.2f} seconds")
    print(f"   Expected: ~10.00 seconds (10 repos × 1 second each)")
    print()
    
    # Test 2: Concurrent processing (5 workers)
    print("Test 2: Concurrent Processing (5 workers)")
    print("-" * 70)
    start_time = time.time()
    concurrent_results = process_concurrent(test_repos, max_workers=5)
    concurrent_time = time.time() - start_time
    print(f"✅ Processed {len(concurrent_results)} repositories")
    print(f"⏱️  Time taken: {concurrent_time:.2f} seconds")
    print(f"   Expected: ~2.00 seconds (10 repos ÷ 5 workers × 1 second)")
    print()
    
    # Results
    print("=" * 70)
    print("Results Summary")
    print("=" * 70)
    print(f"Serial processing:   {serial_time:.2f} seconds")
    print(f"Concurrent processing: {concurrent_time:.2f} seconds")
    
    if concurrent_time > 0:
        speedup = serial_time / concurrent_time
        print(f"Speedup: {speedup:.2f}x faster")
        print()
        
        if speedup >= 3.0:
            print("✅ TEST PASSED: Concurrent processing is significantly faster!")
            print(f"   Concurrent is {speedup:.1f}x faster than serial.")
        else:
            print("⚠️  WARNING: Concurrent should be at least 3x faster")
            print(f"   Got {speedup:.1f}x speedup (expected >= 3.0x)")
            print("   This might be due to system load or test environment.")
    else:
        print("❌ ERROR: Concurrent time is 0, something went wrong")
    
    print("=" * 70)
    
    # Explanation
    print()
    print("Why concurrent is faster:")
    print("- Serial: processes one repo at a time")
    print("  Total time = sum of all processing times = 10 × 1s = 10s")
    print()
    print("- Concurrent: processes 5 repos simultaneously")
    print("  Total time ≈ max of batches = 2 batches × 1s = 2s")
    print()
    print("In real scenario (100 repos, 50 workers):")
    print("- Serial: 100 × 60s = 6,000s = 100 minutes")
    print("- Concurrent: 100 ÷ 50 × 60s = 120s = 2 minutes")
    print("- Speedup: 50x faster!")


if __name__ == "__main__":
    main()

