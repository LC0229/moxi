"""Main entry point for document generation (CLI)."""

import argparse
from pathlib import Path

from core import get_logger, settings
from core.lib import ensure_dir_exists
from doc_generator.core import generate_single_doc, generate_batch_docs

logger = get_logger(__name__)



def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate documentation for repositories")
    parser.add_argument(
        "repo_urls",
        nargs="+",
        help="GitHub repository URLs (one or more)",
    )
    parser.add_argument(
        "--auto-write",
        action="store_true",
        help="Automatically write architecture diagram to repository via GitHub API",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for local files (if not using --auto-write)",
    )
    parser.add_argument(
        "--file-name",
        type=str,
        default="ARCHITECTURE_BY_MOXI.md",
        help="Name of the file to write (default: ARCHITECTURE_BY_MOXI.md)",
    )
    parser.add_argument(
        "--concurrent",
        action="store_true",
        default=True,
        help="Process multiple repositories concurrently (default: True)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Maximum number of concurrent workers (default: 10)",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for document generation (CLI)."""
    args = _parse_args()
    
    logger.info("Starting document generation",
               repos=len(args.repo_urls),
               auto_write=args.auto_write,
               concurrent=args.concurrent)
    
    # Single repository
    if len(args.repo_urls) == 1:
        result = generate_single_doc(
            repo_url=args.repo_urls[0],
            auto_write=args.auto_write,
            file_name=args.file_name,
        )
        
        if result:
            if args.auto_write:
                file_name = result.get('file_name', args.file_name)  # Use file_name from result or fallback to args
                if result.get('written', False):
                    print(f"✅ Successfully generated and wrote {file_name} to {args.repo_urls[0]}")
                else:
                    print(f"⚠️  Generated {file_name} but failed to write to {args.repo_urls[0]}")
                    if result.get('error'):
                        print(f"   Error: {result['error']}")
            else:
                # Write to local file
                if args.output:
                    output_dir = Path(args.output)
                    ensure_dir_exists(output_dir)
                    output_file = output_dir / result["file_name"]
                    output_file.write_text(result["architecture_content"], encoding="utf-8")
                    print(f"✅ Generated {result['file_name']} saved to {output_file}")
                else:
                    # Print to stdout
                    print("\n" + "=" * 70)
                    print("Generated Architecture Diagram:")
                    print("=" * 70)
                    print(result["architecture_content"])
        else:
            print(f"❌ Failed to generate documentation for {args.repo_urls[0]}")
            return
    
    # Multiple repositories
    else:
        results = generate_batch_docs(
            repo_urls=args.repo_urls,
            auto_write=args.auto_write,
            file_name=args.file_name,
            concurrent=args.concurrent,
            max_workers=args.max_workers,
        )
        
        successful = [r for r in results if r]
        failed = len(args.repo_urls) - len(successful)
        
        print(f"\n✅ Successfully generated {len(successful)}/{len(args.repo_urls)} architecture diagrams")
        if failed > 0:
            print(f"❌ Failed to generate {failed} READMEs")
        
        if args.output:
            output_dir = Path(args.output)
            ensure_dir_exists(output_dir)
            for i, result in enumerate(successful, 1):
                repo_name = result["repo_url"].split("/")[-1]
                file_name = result.get("file_name", "README_BY_MOXI.md")
                output_file = output_dir / f"{repo_name}_{file_name}"
                output_file.write_text(result["readme_content"], encoding="utf-8")
                print(f"  - {repo_name}: {output_file}")


if __name__ == "__main__":
    main()

