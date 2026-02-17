"""Document generator module for creating architecture diagrams."""

from doc_generator.core import (
    generate_single_doc,
    generate_batch_docs,
)
from doc_generator.llm.architecture_gen import ArchitectureGenerator

__all__ = [
    "generate_single_doc",
    "generate_batch_docs",
    "ArchitectureGenerator",
]

