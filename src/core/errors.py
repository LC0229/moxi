"""Custom exceptions for Moxi project."""


class MoxiBaseException(Exception):
    """Base exception for all Moxi-related errors."""
    pass


class ImproperlyConfigured(MoxiBaseException):
    """Raised when the application is improperly configured."""
    pass


class RepositoryNotFound(MoxiBaseException):
    """Raised when a repository cannot be found or accessed."""
    pass


class ParsingError(MoxiBaseException):
    """Raised when there's an error parsing repository files."""
    pass


class DatasetGenerationError(MoxiBaseException):
    """Raised when there's an error generating training dataset."""
    pass


class TrainingError(MoxiBaseException):
    """Raised when there's an error during model training."""
    pass


class ModelNotFound(MoxiBaseException):
    """Raised when a trained model cannot be found."""
    pass


class GenerationError(MoxiBaseException):
    """Raised when there's an error generating documentation."""
    pass

