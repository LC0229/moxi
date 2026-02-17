"""Architecture diagram generator using rule-based analysis + GPT-4."""

from typing import Optional

from openai import OpenAI

from core import get_logger, settings
from moxi_analyzer import RepositoryInfo
from moxi_analyzer.architecture.analyzer import analyze_architecture_with_rules

logger = get_logger(__name__)


class ArchitectureGenerator:
    """Generate architecture diagrams using rule-based analysis + GPT-4."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize architecture generator.
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            model: Model ID (defaults to settings.OPENAI_MODEL_ID)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL_ID
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file.")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info("Architecture generator initialized", model=self.model)

    def generate(self, repo_info: RepositoryInfo) -> Optional[str]:
        """
        Generate architecture diagram (Mermaid format) for a repository.
        
        Args:
            repo_info: Repository information from moxi_analyzer
            
        Returns:
            Generated architecture document in Markdown format with Mermaid diagram, or None if failed
        """
        try:
            # Step 1: Rule-based analysis (accurate)
            rule_analysis = analyze_architecture_with_rules(repo_info)
            
            # Log what we detected
            logger.info("Architecture analysis completed",
                       components_count=len(rule_analysis['components']),
                       connections_count=len(rule_analysis['connections']),
                       components=[c['name'] for c in rule_analysis['components']])
            
            # Step 2: Generate Mermaid diagram using GPT-4 (based on rule analysis)
            mermaid_diagram = self._generate_mermaid_diagram(rule_analysis)
            
            if not mermaid_diagram:
                logger.warning("Failed to generate Mermaid diagram", 
                             components=rule_analysis['components'],
                             connections=rule_analysis['connections'])
                return None
            
            # Step 3: Generate explanation using GPT-4
            explanation = self._generate_explanation(rule_analysis, mermaid_diagram)
            
            # Step 4: Combine into architecture document
            architecture_doc = self._format_architecture_doc(
                mermaid_diagram,
                explanation,
                rule_analysis
            )
            
            logger.info("Architecture diagram generated",
                       components=len(rule_analysis['components']),
                       connections=len(rule_analysis['connections']))
            
            return architecture_doc
            
        except Exception as e:
            logger.error("Failed to generate architecture diagram", error=str(e))
            return None

    def _generate_mermaid_diagram(self, rule_analysis: dict) -> Optional[str]:
        """Generate Mermaid diagram using GPT-4 based on rule analysis."""
        try:
            components = rule_analysis['components']
            connections = rule_analysis['connections']
            
            prompt = f"""Generate ONLY a Mermaid architecture diagram. This is NOT a README, NOT documentation, ONLY a diagram.

Components detected:
{self._format_components(components)}

Connections detected:
{self._format_connections(connections)}

CRITICAL: You are generating ONLY Mermaid diagram code. Do NOT generate:
- README content
- "How This Project Works" sections
- "How to Use" sections
- Installation instructions
- Any text explanations
- Only return the Mermaid code

Requirements:
1. Use ONLY the components and connections provided above
2. Generate a hierarchical diagram (graph TB for top-to-bottom layout)
3. Organize components in logical layers:
   - Top: User/Client facing components (API Server, Web Server)
   - Middle: Application/Business Logic components
   - Bottom: Data/Storage components (Database, Cache, Storage)
4. Use component names exactly as provided
5. Show connections with arrows: -->
6. Format: graph TB

Return ONLY the Mermaid code, nothing else. Example:
graph TB
    User[User] --> API[API Server]
    API --> Logic[Business Logic]
    Logic --> DB[(Database)]
    Logic --> Cache[(Cache)]
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an architecture diagram expert. Generate simple, accurate Mermaid diagrams."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent output
            )
            
            mermaid_code = response.choices[0].message.content.strip()
            
            # Clean up - extract Mermaid code if wrapped in code blocks
            if "```mermaid" in mermaid_code:
                mermaid_code = mermaid_code.split("```mermaid")[1].split("```")[0].strip()
            elif "```" in mermaid_code:
                mermaid_code = mermaid_code.split("```")[1].split("```")[0].strip()
            
            return mermaid_code
            
        except Exception as e:
            logger.error("Failed to generate Mermaid diagram", error=str(e))
            return None

    def _generate_explanation(self, rule_analysis: dict, mermaid_diagram: str) -> str:
        """Generate architecture explanation using GPT-4."""
        try:
            components = rule_analysis['components']
            
            prompt = f"""You are generating ONLY an architecture diagram explanation. This is NOT a README.

Components detected:
{self._format_components(components)}

Mermaid diagram:
{mermaid_diagram}

CRITICAL REQUIREMENTS:
1. Write ONLY 2-3 sentences explaining the architecture
2. Describe what each component does and how data flows between them
3. DO NOT write:
   - Installation instructions
   - Usage examples
   - "How to Use" sections
   - "How This Project Works" sections
   - Command-line examples
   - Configuration options
   - Project structure lists
   - Contributing guidelines
   - License information
   - Any README-style content

Example of what you SHOULD write:
"The application uses an API Server to receive user requests, which are processed by Business Logic. The Business Logic interacts with a Database for persistent storage and uses Cache for performance optimization. Asynchronous tasks are handled through a Message Queue and processed by Worker components."

Example of what you MUST NOT write:
"How to Use: Clone the repository, install dependencies, run the application..."
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an architecture diagram generator. You ONLY generate architecture explanations. You NEVER generate README content, installation instructions, usage examples, or any documentation beyond the architecture diagram explanation. If asked for anything else, refuse."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Very low temperature for strict adherence
            )
            
            explanation = response.choices[0].message.content.strip()
            
            # Additional safety check: reject if it contains README keywords
            readme_keywords = ["how to use", "installation", "clone the repository", "pip install", "usage examples", "command-line", "configuration options"]
            if any(keyword in explanation.lower() for keyword in readme_keywords):
                logger.warning("GPT-4 generated README content, using fallback")
                return "This architecture consists of the components shown in the diagram above, with data flowing between them as indicated by the arrows."
            
            return explanation
            
        except Exception as e:
            logger.error("Failed to generate explanation", error=str(e))
            return "This architecture consists of the components shown in the diagram above, with data flowing between them as indicated by the arrows."

    def _format_components(self, components: list) -> str:
        """Format components for prompt."""
        return "\n".join([f"- {c['name']} ({c['type']})" for c in components])

    def _format_connections(self, connections: list) -> str:
        """Format connections for prompt."""
        return "\n".join([f"- {c['from']} → {c['to']}" for c in connections])

    def _format_architecture_doc(self, mermaid_diagram: str, explanation: str, rule_analysis: dict) -> str:
        """Format architecture document - ONLY diagram and explanation, NO README content."""
        from datetime import datetime
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Validate explanation doesn't contain README content
        readme_keywords = ["how to use", "installation", "clone", "pip install", "usage examples", 
                          "command-line", "configuration", "project structure", "contributing", 
                          "license", "how this project works"]
        explanation_lower = explanation.lower()
        if any(keyword in explanation_lower for keyword in readme_keywords):
            logger.warning("Explanation contains README keywords, using minimal fallback")
            explanation = "This architecture consists of the components shown in the diagram above, with data flowing between them as indicated by the arrows."
        
        # Simple format: ONLY diagram and explanation - NO other content
        doc = f"""# Architecture Diagram
Last updated: {current_time}

```mermaid
{mermaid_diagram}
```

## Overview

{explanation}
"""
        
        # Final validation: ensure no README sections
        if any(section in doc.lower() for section in ["how to use", "installation", "usage examples", 
                                                       "project structure", "contributing", "license",
                                                       "how this project works", "command-line example"]):
            logger.error("Generated document contains README content - this should not happen!")
            # Return minimal version
            return f"""# Architecture Diagram
Last updated: {current_time}

```mermaid
{mermaid_diagram}
```

## Overview

This architecture consists of the components shown in the diagram above, with data flowing between them as indicated by the arrows.
"""
        
        return doc

