"""Deduplicator for removing duplicate training samples."""

import hashlib
from typing import Dict, List

from core import get_logger

logger = get_logger(__name__)


class Deduplicator:
    """Remove duplicate samples from dataset."""

    def _compute_hash(self, sample: Dict) -> str:
        """
        Compute hash for a training sample.
        
        Args:
            sample: Training sample dictionary
            
        Returns:
            Hash string
        """
        # Hash based on instruction and output (input may vary slightly)
        key = f"{sample.get('instruction', '')}|{sample.get('output', '')}"
        return hashlib.md5(key.encode()).hexdigest()

    def deduplicate(self, samples: List[Dict]) -> List[Dict]:
        """
        Remove duplicate samples from dataset.
        
        Args:
            samples: List of training samples
            
        Returns:
            Deduplicated list of samples
        """
        logger.info("Deduplicating dataset", total_samples=len(samples))
        
        seen_hashes = set()
        unique_samples = []
        
        for sample in samples:
            sample_hash = self._compute_hash(sample)
            
            if sample_hash not in seen_hashes:
                seen_hashes.add(sample_hash)
                unique_samples.append(sample)
            else:
                logger.debug("Duplicate sample removed", hash=sample_hash[:8])
        
        removed = len(samples) - len(unique_samples)
        logger.info("Deduplication complete",
                   original=len(samples),
                   unique=len(unique_samples),
                   removed=removed)
        
        return unique_samples

