"""
Recommended README structure (from Best-README-Template and common practice).

Use this in Phase 3 instruction prompts and at inference so the model
learns to generate READMEs that follow these sections. Combines with
the learning pattern: (file_tree, project_type) → README content.

Instructional sources (not for data collection; use in prompts only):
- Best-README-Template: https://github.com/othneildrew/Best-README-Template
- Art of README: https://github.com/hackergrrl/art-of-readme (cognitive funneling, checklist)
"""

# Sections to encourage in generated READMEs (Best-README-Template style)
# https://github.com/othneildrew/Best-README-Template
README_SECTIONS = [
    "Title / project name and short description",
    "Table of Contents (optional for long READMEs)",
    "About the Project",
    "Built With (tech stack)",
    "Getting Started (Prerequisites, Installation)",
    "Usage",
    "Roadmap (optional)",
    "Contributing (optional)",
    "License",
    "Contact / Acknowledgments (optional)",
]


def get_readme_structure_prompt_suffix() -> str:
    """
    Text to append to instruction or system prompt so the model follows this structure.
    Use in Phase 3 (instruction generation) and Phase 5 (inference).
    """
    return (
        " The README should include these sections where appropriate: "
        + "; ".join(README_SECTIONS)
        + "."
    )


def get_readme_structure_for_instruction() -> str:
    """
    Shorter snippet for inclusion in per-sample instructions (Phase 3).
    """
    return (
        "Include standard sections: About, Built With, Getting Started, Usage, "
        "License (and optionally Roadmap, Contributing, Contact)."
    )
