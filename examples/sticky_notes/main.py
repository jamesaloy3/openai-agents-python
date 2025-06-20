import asyncio

from .agents import process_text


async def main() -> None:
    text = input("Enter text: ")
    await process_text(text)


if __name__ == "__main__":
    asyncio.run(main())
