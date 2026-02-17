"""Download base model for training."""

from core import get_logger, settings
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = get_logger(__name__)


def main():
    """Download the base model specified in settings."""
    model_id = settings.MODEL_ID
    
    logger.info("Downloading base model", model=model_id)
    
    try:
        # Download tokenizer
        logger.info("Downloading tokenizer", model=model_id)
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            token=settings.HUGGINGFACE_ACCESS_TOKEN,
            trust_remote_code=True,
        )
        logger.info("Tokenizer downloaded successfully")
        
        # Download model
        logger.info("Downloading model", model=model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            token=settings.HUGGINGFACE_ACCESS_TOKEN,
            torch_dtype="auto",
            trust_remote_code=True,
        )
        logger.info("Model downloaded successfully", model=model_id)
        
        print(f"✅ Model downloaded: {model_id}")
        print(f"✅ Model size: ~{model.get_memory_footprint() / 1024**3:.2f} GB")
        
    except Exception as e:
        logger.error("Failed to download model", model=model_id, error=str(e))
        print(f"❌ Failed to download model: {str(e)}")
        raise


if __name__ == "__main__":
    main()



