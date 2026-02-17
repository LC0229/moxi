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
    MODEL_ID: str = "meta-llama/Llama-3.2-3B-Instruct"
    
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
    
    # MongoDB (for collected/training data, like llm-twin-course)
    MONGODB_URI: str = "mongodb://moxi:moxi@localhost:27017"
    MONGODB_DB_NAME: str = "moxi"

    # Qdrant config (for RAG vector database)
    QDRANT_DATABASE_HOST: str = "localhost"
    QDRANT_DATABASE_PORT: int = 6333
    USE_QDRANT_CLOUD: bool = False
    QDRANT_CLOUD_URL: str | None = None
    QDRANT_APIKEY: str | None = None
    
    # RabbitMQ config (for task queue)
    RABBITMQ_DEFAULT_USERNAME: str = "guest"
    RABBITMQ_DEFAULT_PASSWORD: str = "guest"
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_QUEUE_NAME: str = "moxi_doc_generation"
    
    # AWS config (for cloud training / DevOps - optional)
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY: str | None = None
    AWS_SECRET_KEY: str | None = None
    # SageMaker execution role ARN (training job runs as this role)
    AWS_ARN_ROLE: str | None = None
    # S3 bucket for training data and model artifacts (e.g. s3://your-bucket/moxi/)
    AWS_S3_BUCKET: str | None = None
    
    # Data paths (single data/ folder for all pipelines; no "training_data" elsewhere)
    DATA_DIR: str = f"{ROOT_DIR}/data"
    MODELS_DIR: str = f"{ROOT_DIR}/models"
    REPO_CACHE_DIR: str | None = f"{ROOT_DIR}/data/repos"  # Cache for cloned repositories
    
    # Dataset generation config
    MIN_REPO_STARS: int = 100  # Lowered to get more repositories (can be overridden via CLI)
    MAX_REPOS_TO_CRAWL: int = 1000  # GitHub API limit: max 1000 results per search
    DATASET_SIZE: int = 10000

    # Public dataset merge for SFT (like llm-twin-course FineTome-Alpaca)
    MERGE_PUBLIC_DATASET: bool = True
    PUBLIC_DATASET_NAME: str = "mlabonne/FineTome-Alpaca-100k"
    PUBLIC_DATASET_SIZE: int = 10000

    def patch_localhost(self) -> None:
        """Patch settings for local development (if needed)."""
        pass


settings = AppSettings()

