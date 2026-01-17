"""Configuration management for Flow Guardian.

Centralizes environment variable loading and configuration.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class FlowConfig:
    """Flow Guardian configuration loaded from environment."""

    backboard_api_key: Optional[str]
    backboard_base_url: str
    cerebras_api_key: Optional[str]
    personal_thread_id: Optional[str]
    team_thread_id: Optional[str]
    user: str

    @classmethod
    def from_env(cls) -> "FlowConfig":
        """Load configuration from environment variables."""
        return cls(
            backboard_api_key=os.environ.get("BACKBOARD_API_KEY"),
            backboard_base_url=os.environ.get(
                "BACKBOARD_BASE_URL", "https://app.backboard.io/api"
            ),
            cerebras_api_key=os.environ.get("CEREBRAS_API_KEY"),
            personal_thread_id=os.environ.get("BACKBOARD_PERSONAL_THREAD_ID"),
            team_thread_id=os.environ.get("BACKBOARD_TEAM_THREAD_ID"),
            user=os.environ.get("FLOW_GUARDIAN_USER", "unknown"),
        )

    @property
    def backboard_available(self) -> bool:
        """Check if Backboard.io is configured."""
        return bool(self.backboard_api_key and self.personal_thread_id)

    @property
    def team_available(self) -> bool:
        """Check if team memory is configured."""
        return bool(self.backboard_api_key and self.team_thread_id)

    @property
    def cerebras_available(self) -> bool:
        """Check if Cerebras is configured."""
        return bool(self.cerebras_api_key)
