"""SFT (Supervised Fine-Tuning) trainer for model training."""

import json
from pathlib import Path
from typing import Any, Optional

import torch
from datasets import Dataset, load_dataset, concatenate_datasets
from transformers import TrainingArguments
from trl import SFTTrainer

from core import get_logger, settings
from moxi_train.finetune.lora_config import LoRAConfig
from moxi_train.finetune.comet_tracker import CometTracker

logger = get_logger(__name__)

# Try to use unsloth for faster training (like llm-twin-course)
try:
    from unsloth import FastLanguageModel, is_bfloat16_supported
    from unsloth.chat_templates import get_chat_template
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False
    from transformers import AutoModelForCausalLM, AutoTokenizer

# Alpaca template: instruction + optional input + response
ALPACA_TEMPLATE_NO_INPUT = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response:
{response}"""

ALPACA_TEMPLATE_WITH_INPUT = """Below is an instruction that describes a task, paired with an input. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input_text}

### Response:
{response}"""


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
        logger.info("Loading model", model=self.model_name, unsloth=UNSLOTH_AVAILABLE)
        
        if UNSLOTH_AVAILABLE:
            # Use unsloth for faster training (like llm-twin-course)
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_name,
                max_seq_length=self.max_seq_length,
                load_in_4bit=self.load_in_4bit if torch.cuda.is_available() else False,
                dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            )
            
            self.model = FastLanguageModel.get_peft_model(
                self.model,
                r=self.lora_config.r,
                lora_alpha=self.lora_config.lora_alpha,
                lora_dropout=self.lora_config.lora_dropout,
                target_modules=self.lora_config.target_modules,
            )
            
            self.tokenizer = get_chat_template(
                self.tokenizer,
                chat_template="chatml",
            )
        else:
            # Fallback to standard transformers
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            device_map = "auto" if torch.cuda.is_available() else None
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                device_map=device_map,
                trust_remote_code=True,
                load_in_4bit=self.load_in_4bit if torch.cuda.is_available() else False,
            )
            
            from peft import get_peft_model
            peft_config = self.lora_config.to_peft_config()
            self.model = get_peft_model(self.model, peft_config)
        
        logger.info("Model loaded", 
                   model=self.model_name,
                   unsloth=UNSLOTH_AVAILABLE)
        
        return self.model, self.tokenizer

    def _input_to_text(self, inp: Any) -> str:
        """Convert input field to string (dict → JSON or readable; empty → '')."""
        if inp is None or (isinstance(inp, str) and not inp.strip()):
            return ""
        if isinstance(inp, dict):
            # README task: file_tree + project_type
            parts = []
            if "file_tree" in inp:
                tree = inp["file_tree"]
                if isinstance(tree, list):
                    parts.append("File structure:\n" + "\n".join(tree[:200]))  # cap for length
                else:
                    parts.append(str(tree))
            if inp.get("project_type"):
                parts.append("Project type: " + str(inp["project_type"]))
            return "\n\n".join(parts) if parts else json.dumps(inp)
        return str(inp)

    def format_dataset(self, dataset: Dataset) -> Dataset:
        """
        Format dataset for SFT training.
        Supports Alpaca (instruction, output) and README (instruction, input, content).
        """
        def format_samples(examples):
            texts = []
            instructions = examples.get("instruction", [])
            n = len(instructions)
            # Merged dataset: some rows have 'output' (Alpaca), some 'content' (README)
            outputs = examples.get("output", [None] * n)
            contents = examples.get("content", [None] * n)
            if len(outputs) != n:
                outputs = [None] * n
            if len(contents) != n:
                contents = [None] * n
            responses = [
                (o if o is not None and str(o).strip() else c)
                for o, c in zip(outputs, contents, strict=False)
            ]
            inputs = examples.get("input", [None] * n)
            if len(inputs) != n:
                inputs = [None] * n
            for instruction, response, inp in zip(instructions, responses, inputs, strict=False):
                input_text = self._input_to_text(inp)
                if input_text:
                    text = ALPACA_TEMPLATE_WITH_INPUT.format(
                        instruction=instruction,
                        input_text=input_text,
                        response=response,
                    )
                else:
                    text = ALPACA_TEMPLATE_NO_INPUT.format(
                        instruction=instruction,
                        response=response,
                    )
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
        merge_public_dataset: bool = True,
        public_dataset_name: str = "mlabonne/FineTome-Alpaca-100k",
        public_dataset_size: int = 10000,
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
            merge_public_dataset: If True, merge with public instruction dataset (e.g. FineTome-Alpaca)
            public_dataset_name: HuggingFace dataset name for merge
            public_dataset_size: Max number of public samples to merge
        """
        # Load model if not loaded
        if self.model is None or self.tokenizer is None:
            self.load_model()

        # Load custom dataset (Alpaca-style: instruction, optional input, content/output)
        logger.info("Loading dataset", path=dataset_path)
        custom_dataset = load_dataset("json", data_files=dataset_path, split="train")

        # Optionally merge public instruction dataset (like llm-twin-course)
        if merge_public_dataset:
            try:
                static_dataset = load_dataset(
                    public_dataset_name,
                    split=f"train[:{public_dataset_size}]",
                    trust_remote_code=True,
                )
                dataset = concatenate_datasets([custom_dataset, static_dataset])
                logger.info(
                    "Merged public dataset",
                    public=public_dataset_name,
                    public_samples=len(static_dataset),
                    total=len(dataset),
                )
            except Exception as e:
                logger.warning("Could not load public dataset, using custom only", error=str(e))
                dataset = custom_dataset
        else:
            dataset = custom_dataset

        # Format dataset (instruction + optional input + response)
        formatted_dataset = self.format_dataset(dataset)
        
        # Split train/eval (5% test like llm-twin-course)
        split_dataset = formatted_dataset.train_test_split(test_size=0.05)
        train_dataset = split_dataset["train"]
        eval_dataset = split_dataset["test"]
        
        logger.info("Dataset loaded", 
                   train_size=len(train_dataset),
                   eval_size=len(eval_dataset))
        
        # Initialize Comet ML tracker
        comet_tracker = CometTracker(
            experiment_name=f"sft-{Path(output_dir).name}",
        )
        
        # Log hyperparameters
        comet_tracker.log_hyperparameters({
            "model_name": self.model_name,
            "learning_rate": learning_rate,
            "num_train_epochs": num_train_epochs,
            "per_device_train_batch_size": per_device_train_batch_size,
            "gradient_accumulation_steps": gradient_accumulation_steps,
            "max_seq_length": self.max_seq_length,
            "lora_r": self.lora_config.r,
            "lora_alpha": self.lora_config.lora_alpha,
            "lora_dropout": self.lora_config.lora_dropout,
            "load_in_4bit": self.load_in_4bit,
        })
        
        # Determine reporting backend
        report_to = []
        if settings.COMET_API_KEY:
            report_to.append("comet_ml")
        if settings.WANDB_API_KEY:
            report_to.append("wandb")
        if not report_to:
            report_to = None
        
        # Training arguments (match llm-twin-course)
        bf16_supported = UNSLOTH_AVAILABLE and is_bfloat16_supported() if UNSLOTH_AVAILABLE else (torch.cuda.is_available() and torch.cuda.is_bf16_supported())
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            learning_rate=learning_rate,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            fp16=not bf16_supported,
            bf16=bf16_supported,
            logging_steps=1,
            optim="adamw_8bit" if torch.cuda.is_available() else "adamw_torch",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            per_device_eval_batch_size=per_device_train_batch_size,
            warmup_steps=10,
            save_strategy=save_strategy,
            eval_strategy="epoch",
            load_best_model_at_end=True,
            report_to=report_to,
            seed=0,
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
        
        # Save final model (match llm-twin-course format)
        final_model_dir = Path(output_dir) / "final"
        final_model_dir.mkdir(parents=True, exist_ok=True)
        
        if UNSLOTH_AVAILABLE:
            # Use unsloth save method
            self.model.save_pretrained_merged(
                str(final_model_dir), 
                self.tokenizer, 
                save_method="merged_16bit"
            )
        else:
            self.trainer.save_model(str(final_model_dir))
            self.tokenizer.save_pretrained(str(final_model_dir))
        
        # Log model to Comet ML
        comet_tracker.log_model(str(final_model_dir))
        comet_tracker.end()
        
        logger.info("Training complete", final_model=str(final_model_dir))
        
        return self.model, self.tokenizer

