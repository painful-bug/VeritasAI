"""Unsafe feature toggles used by the synthetic violation fixtures."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UnsafePolicy:
    enable_sensitive_profiling: bool = True
    enable_emotion_inference: bool = True
    allow_no_consent_data_use: bool = True
    skip_human_oversight: bool = True
    skip_explanations: bool = True
    retention_days: int = 3650
    auto_apply_decisions: bool = True


POLICY = UnsafePolicy()
