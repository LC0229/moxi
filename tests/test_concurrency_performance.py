"""Test to verify that concurrent processing is faster than serial processing.

NOTE: This test is outdated - SimpleMVPGenerator handles concurrency internally.
"""

import pytest

@pytest.mark.skip(reason="Outdated - use SimpleMVPGenerator instead")
def test_concurrent_vs_serial_performance():
    """This test is outdated. Use SimpleMVPGenerator for dataset generation."""
    pass
