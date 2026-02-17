"""Opik evaluator for document quality assessment (like llm-twin-course)."""

from typing import Dict, List, Optional

try:
    import opik
    from opik.evaluation import evaluate
    from opik.evaluation.metrics import AnswerRelevance, Hallucination
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    opik = None
    evaluate = None
    AnswerRelevance = None
    Hallucination = None

from core import get_logger

logger = get_logger(__name__)


class OpikEvaluator:
    """
    Evaluates generated documentation quality using Opik.
    
    Similar to llm-twin-course's evaluation pipeline.
    
    Metrics:
    - Hallucination: Detects if the generated content contains false information
    - AnswerRelevance: Measures how relevant the answer is to the query
    """

    def __init__(self):
        """Initialize Opik evaluator."""
        if not OPIK_AVAILABLE:
            logger.warning("Opik not available. Install with: pip install opik")
            self.available = False
        else:
            self.available = True
            try:
                self.client = opik.Opik()
                logger.info("Opik evaluator initialized")
            except Exception as e:
                logger.error("Failed to initialize Opik", error=str(e))
                self.available = False

    def evaluate_document(
        self,
        query: str,
        generated_doc: str,
        context: Optional[str] = None,
        repo_info: Optional[Dict] = None,
    ) -> Dict:
        """
        Evaluate a generated document.
        
        Args:
            query: Original query (e.g., "Generate developer guide")
            generated_doc: Generated documentation
            context: Context used for generation (optional)
            repo_info: Repository information (optional)
            
        Returns:
            Dictionary with evaluation results
        """
        if not self.available:
            logger.warning("Opik not available, skipping evaluation")
            return {"error": "Opik not available"}

        try:
            # Prepare evaluation task
            task = {
                "input": {"query": query},
                "context": context or "",
                "output": generated_doc,
            }

            # Define metrics
            metrics = [
                Hallucination(),  # Detect hallucinations
                AnswerRelevance(),  # Measure relevance
            ]

            # Evaluate
            results = evaluate(
                dataset=[task],
                metrics=metrics,
            )

            logger.info("Document evaluation completed",
                       query=query,
                       metrics=len(metrics))

            return {
                "hallucination_score": results.get("hallucination", {}).get("score", 0),
                "relevance_score": results.get("answer_relevance", {}).get("score", 0),
                "results": results,
            }

        except Exception as e:
            logger.error("Evaluation failed", error=str(e))
            return {"error": str(e)}

    def evaluate_batch(
        self,
        tasks: List[Dict],
        dataset_name: Optional[str] = None,
    ) -> Dict:
        """
        Evaluate a batch of documents.
        
        Args:
            tasks: List of evaluation tasks
            dataset_name: Optional dataset name for Opik
            
        Returns:
            Dictionary with batch evaluation results
        """
        if not self.available:
            logger.warning("Opik not available, skipping batch evaluation")
            return {"error": "Opik not available"}

        try:
            # Create dataset if name provided
            if dataset_name:
                dataset = self.client.get_or_create_dataset(
                    name=dataset_name,
                    description="Moxi documentation evaluation dataset",
                )
                dataset.insert(tasks)
                logger.info("Dataset created/updated", name=dataset_name)

            # Evaluate
            metrics = [
                Hallucination(),
                AnswerRelevance(),
            ]

            results = evaluate(
                dataset=tasks,
                metrics=metrics,
            )

            logger.info("Batch evaluation completed",
                       task_count=len(tasks),
                       metrics=len(metrics))

            return results

        except Exception as e:
            logger.error("Batch evaluation failed", error=str(e))
            return {"error": str(e)}

