"""Custom exceptions for the Competitor Ad Analyzer."""


class CompetitorAnalyzerError(Exception):
    """Base exception for all analyzer errors."""
    pass


# Scraping Errors
class ScraperError(CompetitorAnalyzerError):
    """Base exception for scraping errors."""
    pass


class RateLimitError(ScraperError):
    """Raised when rate limit is exceeded."""
    def __init__(self, platform: str, retry_after: int = None):
        self.platform = platform
        self.retry_after = retry_after
        message = f"Rate limit exceeded for {platform}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message)


class AuthenticationError(ScraperError):
    """Raised when authentication fails."""
    pass


class PlatformUnavailableError(ScraperError):
    """Raised when platform is unavailable."""
    def __init__(self, platform: str, status_code: int = None):
        self.platform = platform
        self.status_code = status_code
        message = f"Platform {platform} is unavailable"
        if status_code:
            message += f" (HTTP {status_code})"
        super().__init__(message)


class NoAdsFoundError(ScraperError):
    """Raised when no ads are found for query."""
    def __init__(self, query: str, platform: str):
        self.query = query
        self.platform = platform
        super().__init__(f"No ads found for '{query}' on {platform}")


# Analysis Errors
class AnalysisError(CompetitorAnalyzerError):
    """Base exception for analysis errors."""
    pass


class InvalidImageError(AnalysisError):
    """Raised when image cannot be processed."""
    pass


class APIQuotaExceededError(AnalysisError):
    """Raised when API quota is exceeded."""
    def __init__(self, api_name: str):
        self.api_name = api_name
        super().__init__(f"API quota exceeded for {api_name}")


class ModelError(AnalysisError):
    """Raised when AI model fails."""
    def __init__(self, model: str, message: str):
        self.model = model
        super().__init__(f"Model {model} error: {message}")


# Database Errors
class DatabaseError(CompetitorAnalyzerError):
    """Base exception for database errors."""
    pass


class RecordNotFoundError(DatabaseError):
    """Raised when database record is not found."""
    def __init__(self, model: str, identifier: str):
        self.model = model
        self.identifier = identifier
        super().__init__(f"{model} with ID '{identifier}' not found")


class DuplicateRecordError(DatabaseError):
    """Raised when attempting to create duplicate record."""
    def __init__(self, model: str, identifier: str):
        self.model = model
        self.identifier = identifier
        super().__init__(f"{model} with ID '{identifier}' already exists")


# Configuration Errors
class ConfigurationError(CompetitorAnalyzerError):
    """Raised when configuration is invalid."""
    pass


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is missing."""
    def __init__(self, api_name: str):
        self.api_name = api_name
        super().__init__(f"Missing API key for {api_name}. Set {api_name}_API_KEY environment variable")


# Cost Errors
class CostLimitExceededError(CompetitorAnalyzerError):
    """Raised when cost limit is exceeded."""
    def __init__(self, current_cost: float, limit: float):
        self.current_cost = current_cost
        self.limit = limit
        super().__init__(f"Cost limit exceeded: ${current_cost:.2f} > ${limit:.2f}")
