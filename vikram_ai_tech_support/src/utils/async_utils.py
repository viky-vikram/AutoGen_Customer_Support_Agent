"""Safe execution of coroutines from Streamlit's synchronous script thread.

Streamlit reruns the script in a worker thread that normally has no running
event loop, so ``asyncio.run`` is safe. If a running loop is ever present
(e.g. some hosted environments), the coroutine is executed on a fresh loop in
a dedicated thread instead — avoiding
``RuntimeError: asyncio.run() cannot be called from a running event loop``
without any global event-loop patching.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def run_async(coroutine: Coroutine[Any, Any, T]) -> T:
    """Run ``coroutine`` to completion and return its result."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop in this thread — the normal Streamlit case.
        return asyncio.run(coroutine)

    # A loop is already running in this thread; run the coroutine on its own
    # loop in a separate thread so neither loop is disturbed.
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coroutine)
        return future.result()
