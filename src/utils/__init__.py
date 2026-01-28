"""工具模块"""

from .exceptions import (
    MSearchError,
    ConfigError,
    DatabaseError,
    VectorStoreError,
    EmbeddingError,
    TaskError,
    FileError,
    ModelError,
    HardwareError,
    ValidationError,
    APIError,
    CacheError,
    MediaProcessingError,
    SearchError
)
from .error_handling import ErrorHandler, retry, handle_errors, convert_errors
from .retry import RetryStrategy, retry_on_exception, retry_on_condition, exponential_backoff
from .helpers import (
    generate_uuid,
    calculate_file_hash,
    get_file_extension,
    get_file_size,
    format_file_size,
    ensure_directory,
    safe_filename,
    deep_merge_dict,
    flatten_dict,
    chunk_list,
    truncate_string
)
from .file_utils import (
    get_files_by_extension,
    is_image_file,
    is_video_file,
    is_audio_file,
    ensure_directory_exists,
    safe_delete_file,
    safe_delete_directory,
    copy_file_with_progress,
    get_relative_path,
    is_hidden_file
)

__all__ = [
    # Exceptions
    'MSearchError',
    'ConfigError',
    'DatabaseError',
    'VectorStoreError',
    'EmbeddingError',
    'TaskError',
    'FileError',
    'ModelError',
    'HardwareError',
    'ValidationError',
    'APIError',
    'CacheError',
    'MediaProcessingError',
    'SearchError',
    # Error Handling
    'ErrorHandler',
    'retry',
    'handle_errors',
    'convert_errors',
    # Retry
    'RetryStrategy',
    'retry_on_exception',
    'retry_on_condition',
    'exponential_backoff',
    # Helpers
    'generate_uuid',
    'calculate_file_hash',
    'get_file_extension',
    'get_file_size',
    'format_file_size',
    'ensure_directory',
    'safe_filename',
    'deep_merge_dict',
    'flatten_dict',
    'chunk_list',
    'truncate_string',
    # File Utils
    'get_files_by_extension',
    'is_image_file',
    'is_video_file',
    'is_audio_file',
    'ensure_directory_exists',
    'safe_delete_file',
    'safe_delete_directory',
    'copy_file_with_progress',
    'get_relative_path',
    'is_hidden_file'
]