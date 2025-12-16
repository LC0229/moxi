"""SFT (Supervised Fine-Tuning) trainer for model training."""

from pathlib import Path
from typing import Optional

import torch
from datasets import Dataset, load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
)
from trl import SFTTrainer

from core import get_logger, settings
from training_pipeline.finetune.lora_config import LoRAConfig

logger = get_logger(__name__)

# Alpaca template for instruction following
ALPACA_TEMPLATE = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{}

### Response:
{}"""


class SFTTrainerWrapper:
    """SFT Trainer wrapper for fine-tuning models."""

    def __init__(
        self,
        model_name: str = None,
        lora_config: Optional[LoRAConfig] = None,
        max_seq_length: int = 2048,
        load_in_4bit: bool = False,
    ):
        """
        Initialize SFT trainer.
        
        Args:
            model_name: Base model name (defaults to settings.MODEL_ID)
            lora_config: LoRA configuration (defaults to LoRAConfig())
            max_seq_length: Maximum sequence length
            load_in_4bit: Whether to load model in 4-bit quantization
        """
        self.model_name = model_name or settings.MODEL_ID
        self.lora_config = lora_config or LoRAConfig()
        self.max_seq_length = max_seq_length
        self.load_in_4bit = load_in_4bit
        
        self.model = None
        self.tokenizer = None
        self.trainer = None
        
        logger.info("SFT Trainer initialized", 
                   model=self.model_name,
                   lora_r=self.lora_config.r)

    def load_model(self):
        """Load base model and tokenizer."""
        logger.info("Loading model", model=self.model_name)
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            trust_remote_code=True,
            load_in_4bit=self.load_in_4bit,
        )
        
        # Apply LoRA
        from peft import get_peft_model
        
        peft_config = self.lora_config.to_peft_config()
        self.model = get_peft_model(self.model, peft_config)
        
        logger.info("Model loaded", 
                   model=self.model_name,
                   lora_params=self.model.num_parameters())
        
        return self.model, self.tokenizer

    def format_dataset(self, dataset: Dataset) -> Dataset:
        """
        Format dataset for SFT training.
        
        Args:
            dataset: Dataset with 'instruction' and 'output' fields
            
        Returns:
            Formatted dataset with 'text' field
        """
        def format_samples(examples):
            texts = []
            for instruction, output in zip(
                examples.get("instruction", []),
                examples.get("output", []),
            ):
                text = ALPACA_TEMPLATE.format(instruction, output)
                text += self.tokenizer.eos_token
                texts.append(text)
            
            return {"text": texts}
        
        formatted = dataset.map(
            format_samples,
            batched=True,
            remove_columns=dataset.column_names,
        )
        
        return formatted

    def train(
        self,
        dataset_path: str,
        output_dir: str,
        learning_rate: float = 3e-4,
        num_train_epochs: int = 3,
        per_device_train_batch_size: int = 2,
        gradient_accumulation_steps: int = 8,
        save_strategy: str = "epoch",
    ):
        """
        Train the model using SFT.
        
        Args:
            dataset_path: Path to training dataset JSON file
            output_dir: Directory to save checkpoints
            learning_rate: Learning rate
            num_train_epochs: Number of training epochs
            per_device_train_batch_size: Batch size per device
            gradient_accumulation_steps: Gradient accumulation steps
            save_strategy: Save strategy ("epoch", "steps", etc.)
        """
        # Load model if not loaded
        if self.model is None or self.tokenizer is None:
            self.load_model()
        
        # Load dataset
        logger.info("Loading dataset", path=dataset_path)
        dataset = load_dataset("json", data_files=dataset_path, split="train")
        
        # Format dataset
        formatted_dataset = self.format_dataset(dataset)
        
        # Split train/eval
        split_dataset = formatted_dataset.train_test_split(test_size=0.1)
        train_dataset = split_dataset["train"]
        eval_dataset = split_dataset["test"]
        
        logger.info("Dataset loaded", 
                   train_size=len(train_dataset),
                   eval_size=len(eval_dataset))
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            learning_rate=learning_rate,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            fp16=torch.cuda.is_available() and not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
            logging_steps=10,
            save_strategy=save_strategy,
            eval_strategy="epoch",
            load_best_model_at_end=True,
            report_to="wandb" if settings.WANDB_API_KEY else None,
            warmup_steps=100,
            weight_decay=0.01,
            lr_scheduler_type="cosine",
        )
        
        # Create trainer
        self.trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            args=training_args,
            max_seq_length=self.max_seq_length,
            packing=False,
        )
        
        # Train
        logger.info("Starting training", 
                   epochs=num_train_epochs,
                   batch_size=per_device_train_batch_size)
        
        self.trainer.train()
        
        # Save final model
        final_model_dir = Path(output_dir) / "final"
        final_model_dir.mkdir(parents=True, exist_ok=True)
        
        self.trainer.save_model(str(final_model_dir))
        self.tokenizer.save_pretrained(str(final_model_dir))
        
        logger.info("Training complete", final_model=str(final_model_dir))
        
        return self.model, self.tokenizer

