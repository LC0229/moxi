"""OpenAI-based document generator using GPT-4o-mini."""

from datetime import datetime
from typing import Optional

from openai import OpenAI

from core import get_logger, settings
from repo_analyzer import RepositoryInfo
from doc_generator.utils import (
    read_project_metadata,
    read_key_file_content,
    format_file_tree,
)

logger = get_logger(__name__)

# Prompt template for README generation
README_PROMPT_TEMPLATE = """You are an expert technical writer. Generate a comprehensive README.md file for the following repository.

Repository Information:
- Project Name: {project_name}
- Project Type: {project_type}
- Description: {description}

Project Structure:
```
{file_tree}
```

Key Files:
{key_files}

Code Samples:
{code_samples}

Please generate a README.md that includes:
1. Project title and description (use the actual project name: {project_name})
   IMPORTANT: Add the current timestamp after the title in the format: "Last updated: {current_time}"
2. **How This Project Works** - Explain the architecture, pipeline, and workflow
3. **How to Use** - Step-by-step usage instructions with examples
4. Features (based on the ACTUAL code structure and files shown above)
5. Installation instructions (based on the project structure)
6. Usage examples (based on the code samples provided)
7. Project structure section (use the EXACT structure shown above, formatted as a code block)
8. Contributing guidelines
9. License information (if available)

CRITICAL REQUIREMENTS:
- Use the actual project name "{project_name}" in the README, not generic placeholders like "MyLibrary"
- The project structure section MUST match the actual file tree shown above
- Base ALL content on the ACTUAL code and structure provided, not generic templates
- Make it specific to this project - analyze the actual files and code samples
- For the project structure, use the exact tree format shown above
- **IMPORTANT**: Include a detailed "How This Project Works" section explaining:
  * The overall architecture and pipeline
  * How different components interact
  * The data flow from input to output
- **IMPORTANT**: Include a detailed "How to Use" section with:
  * Step-by-step instructions
  * Command-line examples
  * Configuration options
  * Common use cases
- The title MUST be followed by "Last updated: {current_time}" on the same line or immediately after

Make the README professional, clear, and helpful for users who want to understand and use this project.

Generate only the README content in Markdown format, without any additional explanation or code blocks around it."""


class OpenAIDocGenerator:
    """Document generator using OpenAI GPT-4o-mini."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenAI document generator.
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            model: Model ID (defaults to settings.OPENAI_MODEL_ID)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL_ID
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info("OpenAI document generator initialized", model=self.model)

    def generate(self, repo_info: RepositoryInfo) -> Optional[str]:
        """
        Generate README content for a repository.
        
        Args:
            repo_info: Repository information from repo_analyzer
            
        Returns:
            Generated README content in Markdown format, or None if failed
        """
        try:
            # Read project metadata
            metadata = read_project_metadata(repo_info.path)
            project_name = metadata.get("name") or repo_info.path.name
            description = metadata.get("description") or "No description available"
            
            # Format file tree
            file_tree = format_file_tree(repo_info.all_files, max_depth=4, max_files=80)
            
            # Format key files for prompt
            key_files_str = "\n".join([
                f"- {key}: {path}" 
                for key, path in repo_info.key_files.items()
            ])
            
            # Read sample code from key files
            code_samples = []
            for key, path in list(repo_info.key_files.items())[:3]:  # Limit to 3 files
                content = read_key_file_content(repo_info.path, path, max_lines=30)
                if content:
                    code_samples.append(f"\n### {key} ({path}):\n```\n{content}\n```")
            
            code_samples_str = "\n".join(code_samples) if code_samples else "No code samples available"
            
            # Get current time for timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # Build prompt
            prompt = README_PROMPT_TEMPLATE.format(
                project_name=project_name,
                project_type=repo_info.project_type.value,
                description=description,
                file_tree=file_tree,
                key_files=key_files_str or "No key files detected",
                code_samples=code_samples_str,
                current_time=current_time,
            )
            
            logger.debug("Prompt prepared", 
                        project_name=project_name,
                        file_count=len(repo_info.all_files),
                        key_files_count=len(repo_info.key_files))
            
            logger.info("Generating README", 
                       project_type=repo_info.project_type.value,
                       model=self.model)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert technical writer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.MAX_OUTPUT_TOKENS,
                temperature=0.7,
            )
            
            readme_content = response.choices[0].message.content.strip()
            
            logger.info("README generated", 
                       length=len(readme_content),
                       tokens_used=response.usage.total_tokens)
            
            return readme_content
            
        except Exception as e:
            logger.error("Failed to generate README", error=str(e))
            return None

