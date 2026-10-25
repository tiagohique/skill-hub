import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def running(app: FastAPI) -> AsyncIterator[None]:
    """Executa o lifespan do app numa task própria.

    O servidor MCP usa um task group do anyio, que precisa ser aberto e fechado na mesma
    task; fixtures do pytest-asyncio montam e desmontam em tasks diferentes.
    """
    started = asyncio.Event()
    stop = asyncio.Event()

    async def run() -> None:
        async with app.router.lifespan_context(app):
            started.set()
            await stop.wait()

    task = asyncio.create_task(run())
    waiter = asyncio.create_task(started.wait())
    await asyncio.wait({task, waiter}, return_when=asyncio.FIRST_COMPLETED)
    if task.done():  # falhou ao subir: propaga o erro
        waiter.cancel()
        await task
    try:
        yield
    finally:
        stop.set()
        await task
