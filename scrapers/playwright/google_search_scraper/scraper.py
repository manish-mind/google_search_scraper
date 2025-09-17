import random
import asyncio
from scrapers.db.session import async_session
from scrapers.models.google_scrap import SearchSession
from scrapers.utils.save_utils import save_sponsored_on_page,save_image,save_products_on_page,save_results
from scrapers.utils.user_agents_utils import UserAgent
from scrapers.common.logger_config import get_logger
from scrapers.utils.launch_browers import create_context
from scrapers.utils.save_utils import save_page_screenshot_in_s3,save_images_in_s3

logger=get_logger('scraper')


async def get_google_searched_data(search:str,browser):
    all_results = []
    sponsored_on_page_result=[]
    products_on_page_result=[]
    user_agent_instance = UserAgent()

    context=await create_context(
        browser,
        user_agent=user_agent_instance.create_random(),
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
    # await page.wait_for_selector("h3", timeout=0)

    await save_page_screenshot_in_s3(page,search,path="google_search_screenshot")

    about_block = await page.query_selector("xpath=//div[contains(@class,'xGj8Mb')]")
    async with async_session() as db:
        if about_block:
            about_el = await about_block.query_selector("xpath=//span")
            about = await about_el.inner_text() if about_el else None

            about_info_collect_key = await about_block.query_selector_all(
                "xpath=.//span[contains(@class,'w8qArf FoJoyf')]"
            )
            keys = [await i.inner_text() for i in about_info_collect_key]

            about_info_collect_value = await about_block.query_selector_all(
                "xpath=.//span[contains(@class,'LrzXr kno-fv wHYlTd z8gr9e')]"
            )
            values = [await i.inner_text() for i in about_info_collect_value]

            about_dict = dict(zip(keys, values))
            search_session = SearchSession(
                search_name=search,
                about_info=about_dict,
                about=about
            )
        else:
            logger.info("about section is not available")
            search_session = SearchSession(
                search_name=search,
                about_info={},
                about=None
            )

        db.add(search_session)
        await db.commit()
        await db.refresh(search_session)

    page_no = 1

    while True:
        try:
            sponsored_ads = await page.query_selector_all(
                "xpath=//div[contains(@class,'vdQmEd fP1Qef xpd EtOod pkphOe')]"
            )

            if sponsored_ads:
                for j in sponsored_ads:
                    # Extract each element
                    sponsored_title_el = await j.query_selector("xpath=.//span[contains(@class,'OSrXXb')]")
                    sponsored_title = await sponsored_title_el.inner_text() if sponsored_title_el else None

                    sponsored_subtitle_el = await j.query_selector(
                        "xpath=.//span[contains(@class,'x2VHCd OSrXXb ob9lvb')]")
                    sponsored_subtitle = await sponsored_subtitle_el.inner_text() if sponsored_subtitle_el else None

                    sponsored_heading_el = await j.query_selector(
                        "xpath=.//div[contains(@class,'CCgQ5 vCa9Yd QfkTvb N8QANc MBeuO Va3FIb EE3Upf')]/span")
                    sponsored_heading = await sponsored_heading_el.inner_text() if sponsored_heading_el else None

                    sponsored_des_el = await j.query_selector(
                        "xpath=.//div[contains(@class,'Va3FIb r025kc lVm3ye')]")
                    sponsored_des = await sponsored_des_el.inner_text() if sponsored_des_el else None

                    # Logging instead of print
                    logger.info(f"Sponsored Title: {sponsored_title}")
                    logger.info(f"Sponsored Subtitle: {sponsored_subtitle}")
                    logger.info(f"Sponsored Heading: {sponsored_heading}")
                    logger.info(f"Sponsored Description: {sponsored_des}")
                    print("------")

                    data = {
                        "sponsored_title": sponsored_title,
                        "sponsored_subtitle": sponsored_subtitle,
                        "sponsored_heading": sponsored_heading,
                        "sponsored_description": sponsored_des,
                    }

                    # Only append if at least one field is non-empty
                    if any(field and field.strip() for field in data.values()):
                        sponsored_on_page_result.append(data)
                if sponsored_on_page_result:
                    await save_sponsored_on_page(results=sponsored_on_page_result, session_id=search_session.id)

            products_on_page = await page.query_selector_all(
                "xpath=//div[contains(@jsname,'yZNDdb')]//div[contains(@class,'gXGikb') and @role='listitem']")
            logger.info(f"len of products_on_page: {len(products_on_page)}")

            if products_on_page:
                index = 1
                for i in products_on_page:
                    await asyncio.sleep(random.randint(2, 3))

                    # Image URL
                    image_ele = await i.query_selector(
                        "xpath=.//div[contains(@class,'JK3kIe fUZmuc sjBi9c uhHOwf BYbUcd')]/img"
                    )
                    img_url = await image_ele.get_attribute("src") if image_ele else None
                    logger.info(f"Image URL: {img_url}")

                    if img_url:
                        #---> this is locally we are saving the images
                        # await save_image(img_url, search, page_no, index)
                        #-----> save in s3 bucket
                        asyncio.create_task(
                            save_images_in_s3(img_url, search, idx=index, path="google_product_images", page_no=str(page_no),
                                              is_product=True))

                    pro_name_ele = await i.query_selector("xpath=.//div[contains(@class,'gkQHve SsM98d RmEs5b')]")
                    pro_name = await pro_name_ele.inner_text() if pro_name_ele else None

                    product_price_el = await i.query_selector("xpath=.//div[contains(@class,'FG68Ac RmEs5b')]")
                    pro_price = await product_price_el.inner_text() if product_price_el else None

                    pro_deliver_by_el = await i.query_selector(
                        "xpath=.//div[contains(@class,'n7emVc QgzbTc RmEs5b')]")
                    pro_deliver_by = await pro_deliver_by_el.inner_text() if pro_deliver_by_el else None

                    logger.info(f"Product Name: {pro_name}")
                    logger.info(f"Product Price: {pro_price}")
                    logger.info(f"Deliver By: {pro_deliver_by}")

                    data = {
                        "product_title": pro_name,
                        "product_price": pro_price,
                        "product_deliver_by": pro_deliver_by,
                        "product_image": img_url,
                    }

                    if any(field and field.strip() for field in data.values()):
                        products_on_page_result.append(data)

                    index += 1
                if products_on_page_result:
                    await save_products_on_page(results=products_on_page_result, session_id=search_session.id)

            logger.info(f"\n--- Page {page_no} ---")

            blocks = await page.query_selector_all(
                "(//div[contains(@class,'N54PNb BToiNc')] | //div[contains(@class,'srKDX')] | //div[contains(@jsname,'pKB8Bc')]) | //div[contains(@class,'vdQmEd fP1Qef xpd EtOod pkphOe')]")

            for i in blocks:
                title_el = await i.query_selector(
                    "xpath=.//div[contains(@class,'HGLrXd ojE3Fb')]//span[contains(@class,'VuuXrf')]")
                title = await title_el.inner_text() if title_el else None

                subtitle_el = await i.query_selector(
                    "xpath=.//div[contains(@class,'notranslate ESMNde HGLrXd ojE3Fb')]//cite")
                subtitle = await subtitle_el.inner_text() if subtitle_el else None

                heading_el = await i.query_selector("xpath=.//h3[contains(@class,'LC20lb MBeuO DKV0Md')]")
                heading = await heading_el.inner_text() if heading_el else None

                description_el = await i.query_selector(
                    "xpath=.//div[contains(@class,'VwiC3b yXK7lf p4wth r025kc Hdw6tb')]")
                description = await description_el.inner_text() if description_el else None

                logger.info(f"Title: {title}")
                logger.info(f"Subtitle: {subtitle}")
                logger.info(f"Heading: {heading}")
                logger.info(f"Description: {description}")
                print("------")

                data = {
                    "title": title,
                    "subtitle": subtitle,
                    "heading": heading,
                    "description": description,
                    "is_sponsored": True if sponsored_ads else False,
                    "page_no": page_no
                }
                if any(field and field.strip() for field in [title, subtitle, heading, description]):
                    all_results.append(data)

            next_button = await page.query_selector("a#pnnext")
            if not next_button:
                await save_results(results=all_results, session_id=search_session.id)
                logger.info("No more pages available.")
                break

            await next_button.click()
            await page.wait_for_timeout(2000)  # wait for new page to load
            page_no += 1
            await asyncio.sleep(random.randint(2, 4))
        except Exception as e:
            logger.info(f"Error on page {page_no}: {e}")
            break

    await page.wait_for_timeout(5000)
