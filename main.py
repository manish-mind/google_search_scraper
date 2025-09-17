from scrapers.db.session import engine,Base
from scrapers.playwright import get_google_searched_data,get_google_scrap_search_img
from scrapers.utils.launch_browers import start_browser
import asyncio

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    await init_models()
    browser = await start_browser(
        extra_args=
        [
            '--disable-blink-features',
            "--disk-cache-dir='/tmp/playwright_cache'",
            '--dump-dom'
            '--mute-audio',
            '--use-gl=swiftshader',
            '--enable-accelerated-2d-canvas',
            '--headless-new',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-background-networking',
            '--lang=en-US',
            '--disable-infobars',
            '--disable-extensions',
            '--disable-crash-reporter',
            '--no-first-run',
            '--disable-ipc-flooding-protection',
        ],
    )
    await get_google_searched_data(search='dell laptop', browser=browser)
    # await get_google_scrap_search_img(search="dell laptop",browser=browser)


if __name__ == "__main__":
    asyncio.run(main())