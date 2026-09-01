import asyncio
from db import init_db

async def main():
    await init_db()
    print("Database schema updated with exponential backoff columns.")

if __name__ == '__main__':
    asyncio.run(main())
