"""Dataset validator for quality control."""

from typing import Dict, List

from core import get_logger

logger = get_logger(__name__)


class DatasetValidator:
    """Validate training dataset quality."""

    def __init__(
        self,
        min_instruction_length: int = 20,
        min_output_length: int = 100,
        max_output_length: int = 50000  # Maximum output length for training samples
    ):
        """
        Initialize dataset validator.
        
        Args:
            min_instruction_length: Minimum instruction text length
            min_output_length: Minimum output length
            max_output_length: Maximum output length
        """
        self.min_instruction_length = min_instruction_length
        self.min_output_length = min_output_length
        self.max_output_length = max_output_length

    def validate_sample(self, sample: Dict) -> tuple[bool, List[str]]:
        """
        Validate a single training sample.
        
        Args:
            sample: Training sample dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        if "instruction" not in sample:
            errors.append("Missing 'instruction' field")
        if "input" not in sample:
            errors.append("Missing 'input' field")
        if "output" not in sample:
            errors.append("Missing 'output' field")
        
        if errors:
            return False, errors
        
        # Validate instruction
        instruction = sample["instruction"]
        if not isinstance(instruction, str):
            errors.append("'instruction' must be a string")
        elif len(instruction) < self.min_instruction_length:
            errors.append(f"Instruction too short: {len(instruction)} < {self.min_instruction_length}")
        
        # Validate output
        output = sample["output"]
        if not isinstance(output, str):
            errors.append("'output' must be a string")
        elif len(output) < self.min_output_length:
            errors.append(f"Output too short: {len(output)} < {self.min_output_length}")
        elif len(output) > self.max_output_length:
            errors.append(f"Output too long: {len(output)} > {self.max_output_length}")
        
        # Validate input structure
        input_data = sample["input"]
        if not isinstance(input_data, dict):
            errors.append("'input' must be a dictionary")
        elif "project_type" not in input_data:
            errors.append("'input' missing 'project_type' field")
        
        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_dataset(self, samples: List[Dict]) -> Dict[str, any]:
        """
        Validate entire dataset.
        
        Args:
            samples: List of training samples
            
        Returns:
            Validation report dictionary
        """
        logger.info("Validating dataset", total_samples=len(samples))
        
        valid_samples = []
        invalid_samples = []
        all_errors = []
        
        for i, sample in enumerate(samples):
            is_valid, errors = self.validate_sample(sample)
            
            if is_valid:
                valid_samples.append(sample)
            else:
                invalid_samples.append((i, sample, errors))
                all_errors.extend(errors)
        
        report = {
            "total_samples": len(samples),
            "valid_samples": len(valid_samples),
            "invalid_samples": len(invalid_samples),
            "validation_rate": len(valid_samples) / len(samples) if samples else 0,
            "errors": all_errors[:20],  # First 20 errors
            "error_summary": self._summarize_errors(all_errors)
        }
        
        logger.info("Validation complete",
                   valid=len(valid_samples),
                   invalid=len(invalid_samples),
                   rate=f"{report['validation_rate']:.2%}")
        
        return report

    def _summarize_errors(self, errors: List[str]) -> Dict[str, int]:
        """Summarize error types."""
        summary = {}
        for error in errors:
            # Extract error type (first part before colon or first few words)
            error_type = error.split(":")[0] if ":" in error else error.split()[0]
            summary[error_type] = summary.get(error_type, 0) + 1
        return summary

