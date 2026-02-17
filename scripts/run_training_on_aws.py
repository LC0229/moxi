#!/usr/bin/env python3
"""
Run Moxi training on AWS via SageMaker (LLM course way).

Uses .env AWS_* settings. Uploads SFT data to S3, then either:
  - Submits a SageMaker HuggingFace training job (if AWS_ARN_ROLE set and sagemaker installed),
  - Or prints EC2 commands as fallback.

Usage:
  make train-aws
  Or: PYTHONPATH=src python scripts/run_training_on_aws.py
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"


def _load_settings():
    sys.path.insert(0, str(SRC))
    from core.config import settings
    return settings


def _ensure_data_uploaded(bucket: str, region: str, skip_upload: bool) -> str:
    """Upload data/sft to S3; return S3 URI for training channel."""
    s3_data_prefix = f"s3://{bucket}/moxi/data"
    data_sft = ROOT / "data" / "sft"
    local_dataset = data_sft / "training_dataset.json"

    if not skip_upload:
        if data_sft.exists():
            cmd = ["aws", "s3", "cp", str(data_sft), f"{s3_data_prefix}/sft/", "--recursive"]
            print("Uploading data to S3:", " ".join(cmd))
            subprocess.run(cmd, check=True, cwd=str(ROOT))
        elif local_dataset.exists():
            subprocess.run(
                ["aws", "s3", "cp", str(local_dataset), f"{s3_data_prefix}/sft/training_dataset.json"],
                check=True,
                cwd=str(ROOT),
            )
        else:
            print("No data at data/sft/ or data/sft/training_dataset.json. Run make generate-sft-dataset first.", file=sys.stderr)
            sys.exit(1)
        print("Upload done.\n")

    return f"{s3_data_prefix}/sft"


def _run_sagemaker_job(region: str, role: str, s3_train_uri: str, bucket: str, job_name: str) -> None:
    """Submit a SageMaker HuggingFace training job."""
    try:
        import sagemaker
        from sagemaker.huggingface import HuggingFace
    except ImportError as e:
        print("SageMaker SDK not installed. Run: poetry install --with aws", file=sys.stderr)
        raise SystemExit(1) from e

    # Entry script lives in src/; SageMaker copies source_dir and runs entry_point from there
    entry_point = "sagemaker_train_entry.py"
    if not (SRC / entry_point).exists():
        print(f"Entry script not found: {SRC / entry_point}", file=sys.stderr)
        sys.exit(1)

    estimator = HuggingFace(
        entry_point=entry_point,
        source_dir=str(SRC),
        role=role,
        instance_count=1,
        instance_type="ml.g5.xlarge",
        transformers_version="4.40",
        pytorch_version="2.1",
        py_version="py310",
        output_path=f"s3://{bucket}/moxi/models",
        sagemaker_session=sagemaker.Session(),
    )

    print("Submitting SageMaker training job (this may take a few minutes to start)...")
    estimator.fit({"train": s3_train_uri}, job_name=job_name)
    print(f"Training job completed. Model artifacts: {estimator.model_data}")
    print(f"Or check S3: s3://{bucket}/moxi/models/")


def main():
    parser = argparse.ArgumentParser(description="Run Moxi training on AWS (SageMaker or EC2)")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be done")
    parser.add_argument("--skip-upload", action="store_true", help="Do not upload data (use existing S3 data)")
    parser.add_argument("--ec2", action="store_true", help="Only print EC2 commands; do not submit SageMaker job")
    args = parser.parse_args()

    settings = _load_settings()
    region = getattr(settings, "AWS_REGION", None) or os.environ.get("AWS_REGION", "us-east-1")
    bucket = getattr(settings, "AWS_S3_BUCKET", None) or os.environ.get("AWS_S3_BUCKET")
    role = getattr(settings, "AWS_ARN_ROLE", None) or os.environ.get("AWS_ARN_ROLE")

    if not bucket:
        print("Set AWS_S3_BUCKET in .env. See docs/TRAINING_ON_AWS.md.", file=sys.stderr)
        sys.exit(1)

    s3_data_prefix = f"s3://{bucket}/moxi/data"
    s3_models_prefix = f"s3://{bucket}/moxi/models"

    if args.dry_run:
        print(f"[dry-run] Would upload data/sft to {s3_data_prefix}/sft/")
        print(f"[dry-run] Model output: {s3_models_prefix}/")
        if role and not args.ec2:
            print(f"[dry-run] Would submit SageMaker job (role {role})")
        return 0

    s3_train_uri = _ensure_data_uploaded(bucket, region, args.skip_upload)

    # Prefer SageMaker when role is set (LLM course way)
    if role and not args.ec2:
        job_name = f"moxi-train-{os.environ.get('USER', 'moxi')}"
        try:
            _run_sagemaker_job(region, role, s3_train_uri, bucket, job_name)
            return 0
        except Exception as e:
            print(f"SageMaker submit failed: {e}", file=sys.stderr)
            print("Falling back to EC2 instructions below.\n", file=sys.stderr)

    # Fallback: EC2 instructions
    print("--- Run training on an EC2 GPU instance (e.g. g5.2xlarge) ---\n")
    print("# 1. On the EC2 instance, sync data from S3:")
    print(f"   aws s3 sync {s3_data_prefix}/sft/ /tmp/moxi/data/sft/ --region {region}")
    print()
    print("# 2. Clone repo, install deps, run training:")
    print("   git clone <your-repo> && cd moxi && poetry install")
    print("   cd src && PYTHONPATH=$(pwd) poetry run python -m moxi_train.finetune.main \\")
    print("     --dataset /tmp/moxi/data/sft/training_dataset.json \\")
    print("     --output-dir /tmp/moxi/models/checkpoints")
    print()
    print("# 3. Upload trained model back to S3:")
    print(f"   aws s3 sync /tmp/moxi/models/ {s3_models_prefix}/checkpoints/ --region {region}")
    print()
    print("To use SageMaker instead: set AWS_ARN_ROLE in .env and run: poetry install --with aws")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
