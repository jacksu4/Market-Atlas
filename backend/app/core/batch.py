"""
Batch operations utilities for optimizing external API calls.
"""
import asyncio
from typing import List, Callable, TypeVar, Awaitable
from functools import wraps

T = TypeVar("T")


async def batch_execute(
    tasks: List[Awaitable[T]],
    max_concurrent: int = 5,
    return_exceptions: bool = False
) -> List[T]:
    """
    Execute multiple async tasks with concurrency limit.

    Args:
        tasks: List of awaitable tasks
        max_concurrent: Maximum number of concurrent tasks
        return_exceptions: If True, exceptions are returned instead of raised

    Returns:
        List of results in the same order as input tasks

    Example:
        tasks = [fetch_news(ticker) for ticker in tickers]
        results = await batch_execute(tasks, max_concurrent=3)
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_task(task):
        async with semaphore:
            return await task

    limited_tasks = [limited_task(task) for task in tasks]

    if return_exceptions:
        return await asyncio.gather(*limited_tasks, return_exceptions=True)
    else:
        return await asyncio.gather(*limited_tasks)


async def batch_process(
    items: List[T],
    processor: Callable[[T], Awaitable],
    max_concurrent: int = 5,
    return_exceptions: bool = False
) -> List:
    """
    Process multiple items in batches with concurrency limit.

    Args:
        items: List of items to process
        processor: Async function to process each item
        max_concurrent: Maximum number of concurrent operations
        return_exceptions: If True, exceptions are returned instead of raised

    Returns:
        List of results in the same order as input items

    Example:
        async def fetch_stock_data(ticker: str):
            return await api.get_stock(ticker)

        tickers = ["AAPL", "MSFT", "GOOGL"]
        results = await batch_process(tickers, fetch_stock_data, max_concurrent=2)
    """
    tasks = [processor(item) for item in items]
    return await batch_execute(tasks, max_concurrent, return_exceptions)


def batched(batch_size: int = 100):
    """
    Decorator to automatically batch function calls.

    Example:
        @batched(batch_size=50)
        async def process_stocks(tickers: List[str]):
            # This will be called in batches of 50
            return await fetch_multiple_stocks(tickers)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(items: List, *args, **kwargs):
            if len(items) <= batch_size:
                return await func(items, *args, **kwargs)

            # Split into batches
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_results = await func(batch, *args, **kwargs)
                results.extend(batch_results)

            return results

        return wrapper
    return decorator


class BatchCollector:
    """
    Collects items and processes them in batches.
    Useful for aggregating multiple small requests.
    """
    def __init__(
        self,
        processor: Callable[[List], Awaitable[List]],
        batch_size: int = 10,
        max_wait_seconds: float = 1.0
    ):
        self.processor = processor
        self.batch_size = batch_size
        self.max_wait_seconds = max_wait_seconds
        self.items = []
        self.results_futures = []
        self.flush_task = None

    async def add(self, item) -> Awaitable:
        """Add item to batch and return future for result"""
        future = asyncio.Future()
        self.items.append(item)
        self.results_futures.append(future)

        # Start flush timer if not already started
        if self.flush_task is None:
            self.flush_task = asyncio.create_task(
                self._auto_flush()
            )

        # Flush if batch is full
        if len(self.items) >= self.batch_size:
            await self.flush()

        return future

    async def _auto_flush(self):
        """Auto-flush after max wait time"""
        await asyncio.sleep(self.max_wait_seconds)
        if self.items:
            await self.flush()

    async def flush(self):
        """Process all collected items"""
        if not self.items:
            return

        items_to_process = self.items
        futures_to_complete = self.results_futures

        # Reset state
        self.items = []
        self.results_futures = []
        self.flush_task = None

        try:
            # Process batch
            results = await self.processor(items_to_process)

            # Set results
            for future, result in zip(futures_to_complete, results):
                future.set_result(result)

        except Exception as e:
            # Set exception on all futures
            for future in futures_to_complete:
                future.set_exception(e)
