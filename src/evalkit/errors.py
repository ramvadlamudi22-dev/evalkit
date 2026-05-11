"""EvalKit exception hierarchy.

Every exception we raise inherits from `EvalKitError`. Each leaf class carries a
stable `code: str` (e.g. `provider.transient`) used in logs, metrics, and retry
policies. Rules and exit-code mapping are defined in
docs/architecture/14_ERROR_HANDLING_STRATEGY.md.

Phase 1 ships the leaves the runner and CLI actually need; the remaining leaves
listed in the planning doc land in Phases 2-4 as their callers are written.
"""

from __future__ import annotations


class EvalKitError(Exception):
    """Root of the EvalKit hierarchy. Never raised directly."""

    code: str = "evalkit.error"

    def user_message(self) -> str:
        """Short, redacted, user-safe rendering. Defaults to the exception message."""
        return str(self) or self.code


# ---------- Usage errors (CLI-level user mistake; CLI exit 64) -------------


class UsageError(EvalKitError):
    """User-facing usage error."""

    code = "usage.error"


class ConfigError(UsageError):
    code = "usage.config"


class SuiteValidationError(UsageError):
    """Suite YAML failed validation."""

    code = "usage.suite_validation"


class DatasetValidationError(UsageError):
    """Dataset JSONL failed validation."""

    code = "usage.dataset_validation"


# ---------- Infrastructure errors (outside our control; CLI exit 2) --------


class InfraError(EvalKitError):
    code = "infra.error"


class StorageError(InfraError):
    code = "infra.storage"


class ProviderError(InfraError):
    """Base for all provider-side failures."""

    code = "provider.error"


class TransientProviderError(ProviderError):
    """Retryable transient failure (network blip, 5xx)."""

    code = "provider.transient"


class TimeoutProviderError(TransientProviderError):
    """Provider call exceeded its per-call deadline."""

    code = "provider.timeout"


class RateLimitProviderError(TransientProviderError):
    """Provider rejected the call with a rate-limit signal."""

    code = "provider.rate_limit"


class PermanentProviderError(ProviderError):
    """Non-retryable failure (bad input, auth, 4xx)."""

    code = "provider.permanent"


class AuthProviderError(PermanentProviderError):
    """Authentication failed; no retry will help."""

    code = "provider.auth"


class ProviderConfigError(PermanentProviderError):
    """Caller-supplied provider configuration is invalid."""

    code = "provider.config"


# ---------- Internal errors (bug; CLI exit 70) ----------------------------


class InternalError(EvalKitError):
    """A bug in EvalKit itself."""

    code = "internal.error"
