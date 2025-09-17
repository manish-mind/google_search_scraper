from scrapers.utils.launch_browers import create_context
from scrapers.utils.user_agents_utils import UserAgent
from scrapers.common.logger_config import get_logger
import random
import asyncio
from scrapers.utils.save_utils import save_images_in_s3,save_page_screenshot_in_s3

logger=get_logger('google_scrap_search_image')
async def get_google_scrap_search_img(search:str,browser):
    user_agent_instance = UserAgent()
    context = None
    page = None

    try:
        context = await create_context(
            browser=browser,
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            # timezone_id="Asia/Kolkata",
            # geolocation={"latitude": 37.7749, "longitude": -122.4194},
            # permissions=["geolocation"],
            bypass_csp=True
        )

        page = await context.new_page()

        await page.goto('https://www.google.com/')

        await page.wait_for_timeout(2000)
        #-------> Handle "signed out" popup (optional)
        try:
            signed_out = await page.query_selector(
                'xpath=//div[contains(@class,"XPuBac")]'
            )
            if signed_out:
                buttons = await signed_out.query_selector_all(
                    'xpath=//div[contains(@class,"kHtcsd")]'
                )
                if buttons:
                    await buttons[0].click()
                    logger.info("Clicked signed out button")
        except Exception as e:
            logger.warning(f"Failed to handle signed-out popup: {e}")

        await page.type("xpath=//textarea[contains(@id,'APjFqb')]", search, delay=100)
        await asyncio.sleep(random.randint(5, 12))
        await page.press("xpath=//div[contains(@class,'hvhmMe')]", "Enter")
        await asyncio.sleep(random.randint(5, 12))

        logger.info("Solve CAPTCHA manually if it appears--->")
        await asyncio.sleep(random.randint(5, 7))

        #---> Click "Images" tab
        tabs = await page.query_selector_all("xpath=//div[contains(@jsname,'xBNgKe')]/span")


        for i in tabs:
            text = (await i.inner_text()).strip()
            print(text)
            if text == "Images":
                await i.click()
                break

    # sponsored_images=await page.wait_for_selector("//div[contains(@class,'RnJeZd pla-unit-img-container')]//img",timeout=2500)
    # for i in sponsored_images:
    #     print(await i.inner_text())
    # await page.wait_for_timeout(700000)

        tabs = await page.query_selector_all("xpath=//div[contains(@jsname,'xBNgKe')]/span")
        for i in tabs:
            if (await i.inner_text()).strip() == "Images":
                await i.click()
                logger.info("Clicked Images tab")
                break

        await page.wait_for_timeout(3000)

        await save_page_screenshot_in_s3(page, search, "google_images_screenshots")

        #Collect images
        image_urls = set()
        max_idle_rounds = 3
        idle_rounds=0

        last_height = await page.evaluate("document.body.scrollHeight")

        while idle_rounds < max_idle_rounds:
            # scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

            containers = await page.query_selector_all(
                "//div[contains(@class,'H8Rx8c')]//img"
            )

            before_count = len(image_urls)
            for img in containers:
                src = await img.get_attribute("src")
                if src and src.startswith("http"):
                    image_urls.add(src)

            # check if new images were added
            if len(image_urls) == before_count:
                idle_rounds += 1
                logger.info(f"No new images, idle_rounds={idle_rounds}")
            else:
                idle_rounds = 0  # reset if new images loaded

            # check if page stopped growing
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                logger.info("Reached end of page.")
                break
            last_height = new_height

        logger.info(f"Collected {len(image_urls)} preview image URLs")
        tasks = [
            save_images_in_s3(url, search, idx=idx, path="google_images")
            for idx, url in enumerate(image_urls, start=1)
        ]
        await asyncio.gather(*tasks)
        await page.wait_for_timeout(5000)
    except Exception as e:
        logger.error(f"Error in get_google_scrap_search_img({search}): {e}", exc_info=True)
    finally:
        if page:
            await page.close()
        if context:
            await context.close()


