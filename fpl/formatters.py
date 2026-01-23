"""Utility functions for formatting data for display."""


def format_rank_compact(rank: int) -> str:
    """Format rank with 3 significant digits and k/M suffix.
    
    Examples:
        1234 -> 1.23k
        23456 -> 23.4k
        345678 -> 345k
        4567890 -> 4.56M
        56789012 -> 56.7M
        678901234 -> 678M
    """
    if rank >= 100_000_000:
        # 100M+: show as whole millions (e.g., 123M)
        return f"{rank // 1_000_000}M"
    elif rank >= 10_000_000:
        # 10M-99.9M: show 1 decimal place (e.g., 56.7M)
        return f"{rank / 1_000_000:.1f}M"
    elif rank >= 1_000_000:
        # 1M-9.99M: show 2 decimal places (e.g., 4.56M)
        return f"{rank / 1_000_000:.2f}M"
    elif rank >= 100_000:
        # 100k-999k: show as whole thousands (e.g., 345k)
        return f"{rank // 1000}k"
    elif rank >= 10_000:
        # 10k-99.9k: show 1 decimal place (e.g., 23.4k)
        return f"{rank / 1000:.1f}k"
    elif rank >= 1000:
        # 1k-9.99k: show 2 decimal places (e.g., 1.23k)
        return f"{rank / 1000:.2f}k"
    else:
        # < 1k: show as-is
        return str(rank)
