"""Main entry point for SFT training."""

import argparse
from pathlib import Path

from core import get_logger, settings
from core.lib import ensure_dir_exists
from moxi_train.finetune.lora_config import LoRAConfig
from moxi_train.finetune.sft_trainer import SFTTrainerWrapper

logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train model using SFT")
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help=f"Path to training dataset (default: {settings.DATA_DIR}/sft/training_dataset.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help=f"Output directory for checkpoints (default: {settings.MODELS_DIR}/checkpoints)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=f"Base model name (default: {settings.MODEL_ID})",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3)",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=3e-4,
        help="Learning rate (default: 3e-4)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
        help="Batch size per device (default: 2)",
    )
    parser.add_argument(
        "--gradient-accumulation-steps",
        type=int,
        default=8,
        help="Gradient accumulation steps (default: 8)",
    )
    parser.add_argument(
        "--no-public-dataset",
        action="store_true",
        help="Disable merging public instruction dataset (e.g. FineTome-Alpaca)",
    )
    parser.add_argument(
        "--public-dataset",
        type=str,
        default=None,
        help="HuggingFace dataset name for merge (default: from settings, e.g. mlabonne/FineTome-Alpaca-100k)",
    )
    parser.add_argument(
        "--public-dataset-size",
        type=int,
        default=None,
        help="Max number of public samples to merge (default: from settings, e.g. 10000)",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for SFT training."""
    args = _parse_args()
    
    # Set defaults
    dataset_path = args.dataset or str(
        Path(settings.DATA_DIR) / "sft" / "training_dataset.json"
    )
    output_dir = args.output_dir or str(Path(settings.MODELS_DIR) / "checkpoints")
    model_name = args.model or settings.MODEL_ID
    
    ensure_dir_exists(output_dir)
    
    logger.info("Starting SFT training",
               dataset=dataset_path,
               model=model_name,
               output_dir=output_dir,
               epochs=args.epochs)
    
    # Initialize trainer
    lora_config = LoRAConfig()
    trainer = SFTTrainerWrapper(
        model_name=model_name,
        lora_config=lora_config,
        max_seq_length=settings.MAX_TOTAL_TOKENS,
        load_in_4bit=False,  # Set to True for QLoRA
    )
    
    # Train
    merge_public = not args.no_public_dataset
    trainer.train(
        dataset_path=dataset_path,
        output_dir=output_dir,
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        merge_public_dataset=merge_public,
        public_dataset_name=args.public_dataset or settings.PUBLIC_DATASET_NAME,
        public_dataset_size=args.public_dataset_size if args.public_dataset_size is not None else settings.PUBLIC_DATASET_SIZE,
    )
    
    logger.info("Training complete", output_dir=output_dir)
    print(f"✅ Training complete! Model saved to {output_dir}/final")


if __name__ == "__main__":
    main()

