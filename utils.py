import asyncio


async def gather_tasks(data: list, func):
    tasks = [func(obj) for obj in data]
    await asyncio.gather(*tasks)
