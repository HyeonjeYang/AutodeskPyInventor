"""Assembly placeholders."""

from __future__ import annotations


class Assembly:
    """Assembly automation is intentionally outside the first package scope."""

    @classmethod
    def new(cls) -> "Assembly":
        raise NotImplementedError(
            "Assembly generation is not part of this reliability-first geometry builder yet."
        )
