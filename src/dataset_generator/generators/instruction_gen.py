"""Instruction generator using GPT-4 to create training samples."""

import json
from pathlib import Path
from typing import Dict, Optional

from openai import OpenAI

from core import get_logger, settings
from core.errors import ImproperlyConfigured
from repo_analyzer import RepositoryInfo

logger = get_logger(__name__)


class InstructionGenerator:
    """Generate training instructions using GPT-4."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize instruction generator.
        
        Args:
            api_key: OpenAI API key. If None, uses settings.OPENAI_API_KEY.
            model: OpenAI model ID. If None, uses settings.OPENAI_MODEL_ID.
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ImproperlyConfigured("OPENAI_API_KEY must be set in .env file")
        
        self.model = model or settings.OPENAI_MODEL_ID
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info("Instruction generator initialized", model=self.model)

    def _create_system_prompt(self) -> str:
        """Create system prompt for GPT-4."""
        return """You are an expert technical writer specializing in creating high-quality documentation for software projects.

Your task is to generate a clear, concise instruction that would lead to creating the given README/documentation.

The instruction should:
1. Be specific and actionable
2. Reference the project structure and key files
3. Focus on what documentation should be generated
4. Be suitable for training an AI model to generate similar documentation

Return ONLY a JSON object with this structure:
{
    "instruction": "Generate a comprehensive README for a Python library project...",
    "reasoning": "Brief explanation of why this instruction is appropriate"
}
"""

    def _create_user_prompt(self, repo_info: RepositoryInfo, readme_content: str) -> str:
        """
        Create user prompt with repository information.
        
        Args:
            repo_info: Repository analysis information
            readme_content: Existing README content (as reference)
            
        Returns:
            Formatted prompt string
        """
        # Extract key information
        project_type = repo_info.project_type.value
        key_files = list(repo_info.key_files.keys())
        
        # Build project structure summary
        structure_summary = f"Project Type: {project_type}\n"
        structure_summary += f"Key Files: {', '.join(key_files[:10])}"  # Limit to first 10
        
        prompt = f"""Given the following repository information and its existing README, generate an instruction that would lead to creating this documentation.

Repository Information:
{structure_summary}

Existing README (reference):
{readme_content[:2000]}  # Limit README preview to 2000 chars

Generate an instruction that describes what documentation should be created for this project."""
        
        return prompt

    def generate_sample(
        self, 
        repo_info: RepositoryInfo, 
        readme_content: str
    ) -> Dict[str, str]:
        """
        Generate a training sample from repository information.
        
        Args:
            repo_info: Repository analysis information
            readme_content: Existing README content (as the "output")
            
        Returns:
            Training sample dictionary with instruction, input, and output
        """
        logger.info("Generating training sample", 
                   repo=str(repo_info.path),
                   project_type=repo_info.project_type.value)
        
        try:
            # Create prompts
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(repo_info, readme_content)
            
            # Call GPT-4
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            instruction = result.get("instruction", "")
            
            # Create training sample
            sample = {
                "instruction": instruction,
                "input": {
                    "project_type": repo_info.project_type.value,
                    "key_files": {k: str(v) for k, v in repo_info.key_files.items()},
                    "repo_path": str(repo_info.path)
                },
                "output": readme_content
            }
            
            logger.info("Training sample generated", 
                       instruction_length=len(instruction),
                       output_length=len(readme_content))
            
            return sample
            
        except Exception as e:
            logger.error("Failed to generate training sample", 
                        repo=str(repo_info.path),
                        error=str(e))
            raise

    def generate_batch(
        self,
        repo_infos: list[tuple[RepositoryInfo, str]],
        batch_size: int = 5
    ) -> list[Dict[str, str]]:
        """
        Generate training samples in batches.
        
        Args:
            repo_infos: List of (RepositoryInfo, readme_content) tuples
            batch_size: Number of samples to generate before saving
            
        Returns:
            List of training samples
        """
        all_samples = []
        
        for i, (repo_info, readme_content) in enumerate(repo_infos, 1):
            try:
                sample = self.generate_sample(repo_info, readme_content)
                all_samples.append(sample)
                
                logger.info("Batch progress", 
                           current=i, 
                           total=len(repo_infos),
                           success=len(all_samples))
                
            except Exception as e:
                logger.warning("Skipped sample generation", 
                             repo=str(repo_info.path),
                             error=str(e))
                continue
        
        logger.info("Batch generation complete", 
                   total=len(repo_infos),
                   successful=len(all_samples))
        
        return all_samples

