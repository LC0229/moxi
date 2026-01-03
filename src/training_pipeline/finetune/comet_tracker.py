"""Comet ML experiment tracking integration."""

from typing import Optional

from comet_ml import Experiment

from core import get_logger, settings

logger = get_logger(__name__)


class CometTracker:
    """Comet ML experiment tracker wrapper."""

    def __init__(
        self,
        experiment_name: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace: Optional[str] = None,
        project_name: Optional[str] = None,
    ):
        """
        Initialize Comet ML tracker.
        
        Args:
            experiment_name: Name of the experiment
            api_key: Comet ML API key (defaults to settings.COMET_API_KEY)
            workspace: Comet ML workspace (defaults to settings.COMET_WORKSPACE)
            project_name: Project name (defaults to settings.COMET_PROJECT)
        """
        self.api_key = api_key or settings.COMET_API_KEY
        self.workspace = workspace or settings.COMET_WORKSPACE
        self.project_name = project_name or settings.COMET_PROJECT
        self.experiment_name = experiment_name
        
        self.experiment: Optional[Experiment] = None
        
        if not self.api_key:
            logger.warning("Comet ML API key not provided, tracking disabled")
            return
        
        try:
            self.experiment = Experiment(
                api_key=self.api_key,
                workspace=self.workspace,
                project_name=self.project_name,
            )
            
            if self.experiment_name:
                self.experiment.set_name(self.experiment_name)
            
            logger.info("Comet ML tracker initialized",
                       workspace=self.workspace,
                       project=self.project_name)
        except Exception as e:
            logger.error("Failed to initialize Comet ML tracker", error=str(e))
            self.experiment = None

    def log_hyperparameters(self, hyperparameters: dict):
        """Log hyperparameters to Comet ML."""
        if self.experiment:
            try:
                self.experiment.log_parameters(hyperparameters)
                logger.debug("Logged hyperparameters", count=len(hyperparameters))
            except Exception as e:
                logger.error("Failed to log hyperparameters", error=str(e))

    def log_metrics(self, metrics: dict, step: Optional[int] = None):
        """Log metrics to Comet ML."""
        if self.experiment:
            try:
                for key, value in metrics.items():
                    self.experiment.log_metric(key, value, step=step)
                logger.debug("Logged metrics", count=len(metrics), step=step)
            except Exception as e:
                logger.error("Failed to log metrics", error=str(e))

    def log_model(self, model_path: str, model_name: Optional[str] = None):
        """Log model artifact to Comet ML."""
        if self.experiment:
            try:
                self.experiment.log_model(model_name or "moxi-model", model_path)
                logger.info("Logged model artifact", path=model_path)
            except Exception as e:
                logger.error("Failed to log model", error=str(e))

    def end(self):
        """End the experiment."""
        if self.experiment:
            try:
                self.experiment.end()
                logger.info("Comet ML experiment ended")
            except Exception as e:
                logger.error("Failed to end experiment", error=str(e))

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.end()

