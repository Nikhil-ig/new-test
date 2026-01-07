"""
Configuration for Centralized API
"""

import os
from typing import Optional

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

MONGODB_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGODB_PORT = int(os.getenv("MONGODB_PORT", 27018))
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "telegram_bot")
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME", "")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "")

# Connection string
if MONGODB_USERNAME and MONGODB_PASSWORD:
    MONGODB_URI = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}"
else:
    MONGODB_URI = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}"

# ============================================================================
# RETRY CONFIGURATION
# ============================================================================

# Exponential backoff base (seconds)
BACKOFF_BASE = float(os.getenv("BOT_BACKOFF_BASE", "1.0"))

# Maximum number of retries
MAX_RETRIES = int(os.getenv("BOT_MAX_RETRIES", "3"))

# Maximum backoff time (seconds)
MAX_BACKOFF = float(os.getenv("BOT_MAX_BACKOFF", "60.0"))

# ============================================================================
# PERFORMANCE CONFIGURATION
# ============================================================================

# Batch operation timeout (seconds)
BATCH_TIMEOUT = float(os.getenv("BATCH_TIMEOUT", "30.0"))

# Maximum concurrent actions
MAX_CONCURRENT_ACTIONS = int(os.getenv("MAX_CONCURRENT_ACTIONS", "100"))

# ============================================================================
# API CONFIGURATION
# ============================================================================

# API host
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# API port
API_PORT = int(os.getenv("API_PORT", "8000"))

# API prefix
API_PREFIX = "/api/v1"

# Rate limit (requests per minute)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# VALIDATION CONFIGURATION
# ============================================================================

# Minimum mute duration (seconds)
MIN_MUTE_DURATION = int(os.getenv("MIN_MUTE_DURATION", "60"))

# Maximum purge message count
MAX_PURGE_COUNT = int(os.getenv("MAX_PURGE_COUNT", "10000"))

# Maximum role name length
MAX_ROLE_NAME_LENGTH = int(os.getenv("MAX_ROLE_NAME_LENGTH", "50"))

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Enable action persistence
ENABLE_PERSISTENCE = os.getenv("ENABLE_PERSISTENCE", "true").lower() == "true"

# Enable dead letter queue
ENABLE_DEAD_LETTER = os.getenv("ENABLE_DEAD_LETTER", "true").lower() == "true"

# Enable automatic retries
ENABLE_AUTO_RETRIES = os.getenv("ENABLE_AUTO_RETRIES", "true").lower() == "true"

# Enable action history
ENABLE_HISTORY = os.getenv("ENABLE_HISTORY", "true").lower() == "true"

# ============================================================================
# DATABASE COLLECTIONS
# ============================================================================

COLLECTION_ACTIONS = "action_logs"
COLLECTION_DEAD_LETTERS = "action_dead_letters"
COLLECTION_WARNINGS = "user_warnings"
COLLECTION_ROLES = "user_roles"

# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_TIMEOUT = int(os.getenv("TELEGRAM_API_TIMEOUT", "30"))

# ============================================================================
# REDIS CONFIGURATION (for integration with bot)
# ============================================================================

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

REDIS_URI = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# ============================================================================
# VALIDATION ERRORS
# ============================================================================

VALIDATION_ERRORS = {
    "INVALID_GROUP_ID": "Group ID must be a negative integer (Telegram group ID format)",
    "INVALID_USER_ID": "User ID must be a positive integer",
    "INVALID_MESSAGE_ID": "Message ID must be a positive integer",
    "INVALID_DURATION": "Duration must be at least 60 seconds",
    "INVALID_REASON": "Reason is required for this action",
    "INVALID_ROLE": "Role name must be 1-50 characters",
    "USER_NOT_FOUND": "User not found in group",
    "MESSAGE_NOT_FOUND": "Message not found",
    "INSUFFICIENT_PERMISSIONS": "Bot does not have required permissions",
    "ACTION_FAILED": "Action execution failed",
}
