from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = str(Path(__file__).parent.parent.parent)


class AppSettings(BaseSettings):
    """Application settings for Moxi project."""
    
    model_config = SettingsConfigDict(env_file=f"{ROOT_DIR}/.env", env_file_encoding="utf-8")

    # Project Info
    PROJECT_NAME: str = "moxi"
    ENVIRONMENT: str = "development"

    # OpenAI config (for dataset generation)
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL_ID: str = "gpt-4o-mini"

    # GitHub config (for repo crawling)
    GITHUB_TOKEN: str | None = None
    
    # Hugging Face config (for model training/inference)
    HUGGINGFACE_ACCESS_TOKEN: str | None = None
    MODEL_ID: str = "meta-llama/Llama-3.1-8B-Instruct"
    
    # Training config
    MAX_INPUT_TOKENS: int = 2048
    MAX_OUTPUT_TOKENS: int = 1024
    MAX_TOTAL_TOKENS: int = 3072
    
    # Embeddings config (optional, for future RAG features)
    EMBEDDING_MODEL_ID: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_SIZE: int = 384
    EMBEDDING_MODEL_DEVICE: str = "cpu"
    
    # Weights & Biases / CometML config (for experiment tracking)
    WANDB_API_KEY: str | None = None
    WANDB_PROJECT: str = "moxi"
    COMET_API_KEY: str | None = None
    COMET_WORKSPACE: str | None = None
    COMET_PROJECT: str = "moxi"
    
    # AWS config (for cloud deployment - optional)
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY: str | None = None
    AWS_SECRET_KEY: str | None = None
    AWS_ARN_ROLE: str | None = None
    
    # Data paths
    DATA_DIR: str = f"{ROOT_DIR}/data"
    TRAINING_DATA_DIR: str = f"{ROOT_DIR}/training_data"
    MODELS_DIR: str = f"{ROOT_DIR}/models"
    
    # Dataset generation config
    MIN_REPO_STARS: int = 100
    MAX_REPOS_TO_CRAWL: int = 100
    DATASET_SIZE: int = 10000

    def patch_localhost(self) -> None:
        """Patch settings for local development (if needed)."""
        pass


settings = AppSettings()

