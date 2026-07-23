class NoOpLimiter:
    """A no‑op rate limiter that always allows the request."""

    async def check_rate_limit(self, key: str, limit: int, period: int = 60) -> None:
        """Placeholder that does nothing and always returns None."""
        return None

# Global instance
limiter = NoOpLimiter()
