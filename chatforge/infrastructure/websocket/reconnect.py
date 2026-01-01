"""Reconnection policies for WebSocket client."""

import random
from abc import ABC, abstractmethod


class ReconnectPolicy(ABC):
    """Abstract reconnection policy."""

    @abstractmethod
    def next_delay(self, attempt: int) -> float | None:
        """
        Get delay before next reconnection attempt.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds, or None to stop reconnecting
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset policy state after successful connection."""
        ...


class ExponentialBackoff(ReconnectPolicy):
    """
    Exponential backoff with jitter.

    Delay = min(base * factor^(attempt-1), max_delay) +/- jitter

    Args:
        base: Initial delay in seconds
        factor: Multiplier for each attempt
        max_delay: Maximum delay cap
        max_attempts: Maximum attempts (0 = infinite)
        jitter: Randomization factor (0.1 = +/-10%)
    """

    def __init__(
        self,
        base: float = 1.0,
        factor: float = 2.0,
        max_delay: float = 60.0,
        max_attempts: int = 5,
        jitter: float = 0.1,
    ):
        self.base = base
        self.factor = factor
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self.jitter = jitter

    def next_delay(self, attempt: int) -> float | None:
        if self.max_attempts > 0 and attempt > self.max_attempts:
            return None

        delay = min(self.base * (self.factor ** (attempt - 1)), self.max_delay)

        # Add jitter
        if self.jitter > 0:
            jitter_range = delay * self.jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def reset(self) -> None:
        pass


class NoReconnect(ReconnectPolicy):
    """Never reconnect - use when reconnection is handled at higher level."""

    def next_delay(self, attempt: int) -> float | None:
        return None

    def reset(self) -> None:
        pass


class FixedDelay(ReconnectPolicy):
    """
    Fixed delay between reconnection attempts.

    Args:
        delay: Seconds to wait between attempts
        max_attempts: Maximum attempts (0 = infinite)
    """

    def __init__(self, delay: float = 5.0, max_attempts: int = 10):
        self.delay = delay
        self.max_attempts = max_attempts

    def next_delay(self, attempt: int) -> float | None:
        if self.max_attempts > 0 and attempt > self.max_attempts:
            return None
        return self.delay

    def reset(self) -> None:
        pass
