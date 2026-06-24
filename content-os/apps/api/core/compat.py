"""Python 3.8 compatibility shims."""
from __future__ import annotations

import asyncio
import functools

if hasattr(asyncio, "to_thread"):
    to_thread = asyncio.to_thread
else:
    async def to_thread(func, *args, **kwargs):
        """Polyfill for asyncio.to_thread (Python 3.9+)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
