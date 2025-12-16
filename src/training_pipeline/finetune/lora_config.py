"""LoRA configuration for efficient fine-tuning."""

from dataclasses import dataclass
from typing import List


@dataclass
class LoRAConfig:
    """LoRA (Low-Rank Adaptation) configuration for efficient fine-tuning."""

    r: int = 32
    """LoRA rank (low-rank matrix rank). Lower rank = fewer parameters = faster training."""
    
    lora_alpha: int = 32
    """LoRA alpha (scaling parameter). Typically set to r or 2*r."""
    
    lora_dropout: float = 0.0
    """LoRA dropout rate."""
    
    target_modules: List[str] = None
    """Target modules to apply LoRA. If None, uses default for Llama models."""
    
    bias: str = "none"
    """Bias type: 'none', 'all', or 'lora_only'."""
    
    task_type: str = "CAUSAL_LM"
    """Task type for PEFT."""
    
    def __post_init__(self):
        """Set default target modules for Llama models if not provided."""
        if self.target_modules is None:
            self.target_modules = [
                "q_proj",
                "k_proj",
                "v_proj",
                "up_proj",
                "down_proj",
                "o_proj",
                "gate_proj",
            ]
    
    def to_peft_config(self):
        """Convert to PEFT LoraConfig."""
        from peft import LoraConfig as PEFTLoraConfig
        
        return PEFTLoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            target_modules=self.target_modules,
            lora_dropout=self.lora_dropout,
            bias=self.bias,
            task_type=self.task_type,
        )

