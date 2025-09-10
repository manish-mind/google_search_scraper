import asyncio
from playwright.async_api import async_playwright
from scrapers.db.session import async_session,engine,Base
from scrapers.models.google_scrap import SearchResult

async def save_to_db(title, subtitle, heading, description):
    async with async_session() as session:
        new_result = SearchResult(
            title=title,
            subtitle=subtitle,
            heading=heading,
            description=description
        )
        session.add(new_result)
        await session.commit()
def normalize_value(value: str | None):
    return None if value in (None, "N/A", "") else value


async def save_results(results: list[dict]):
    async with async_session() as session:
        try:
            objects = [SearchResult(
                title=normalize_value(r.get("title")),
                subtitle=normalize_value(r.get("subtitle")),
                heading=normalize_value(r.get("heading")),
                description=normalize_value(r.get("description")),
            ) for r in results]
            session.add_all(objects)
            await session.commit()

        except Exception as e:
            await session.rollback()
            print(f'Error: {e}')



async def get_google_searched_data(search:str):
    all_results = []
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto('https://www.google.com/')
        signed_out=await page.wait_for_selector('xpath=//div[contains(@class,"XPuBac")]')
        buttons=await signed_out.query_selector_all('xpath=//div[contains(@class,"kHtcsd")]')

        if buttons[0]:
            await buttons[0].click() # here we are clik on the signed out button

        await page.type("xpath=//textarea[contains(@id,'APjFqb')]",search,delay=100)

        await page.press("xpath=//div[contains(@class,'hvhmMe')]", "Enter")

        print("Solve CAPTCHA manually if it appears--->")
        await page.wait_for_selector("h3", timeout=0)



        page_no = 1

        while True:
            print(f"\n--- Page {page_no} ---")
            blocks = await page.query_selector_all(
                "(//div[contains(@class,'N54PNb BToiNc')] | //div[contains(@class,'srKDX')] | //div[contains(@jsname,'pKB8Bc')])")
            for i in blocks:
                title_el = await i.query_selector(
                    "xpath=.//div[contains(@class,'HGLrXd ojE3Fb')]//span[contains(@class,'VuuXrf')]")
                title = await title_el.inner_text() if title_el else "N/A"

                subtitle_el = await i.query_selector(
                    "xpath=.//div[contains(@class,'notranslate ESMNde HGLrXd ojE3Fb')]//cite")
                subtitle = await subtitle_el.inner_text() if subtitle_el else "N/A"

                heading_el = await i.query_selector("xpath=.//h3[contains(@class,'LC20lb MBeuO DKV0Md')]")
                heading = await heading_el.inner_text() if heading_el else "N/A"

                description_el = await i.query_selector(
                    "xpath=//div[contains(@class,'VwiC3b yXK7lf p4wth r025kc Hdw6tb')]")
                description = await description_el.inner_text() if description_el else "N/A"

                print(f"Title: {title}")
                print(f"subtitle: {subtitle}")
                print(f"heading: {heading}")
                print(f"description: {description}")
                print("------")
                all_results.append(
                    {
                        "title": title,
                        "subtitle": subtitle,
                        "heading": heading,
                        "description": description,
                    }
                )

            next_button = await page.query_selector("a#pnnext")
            if not next_button:
                await save_results(results=all_results)
                print("No more pages available.")
                break

            # Go to next page
            await next_button.click()
            await page.wait_for_timeout(2000)  # wait for new page to load
            page_no += 1

        await page.wait_for_timeout(700000)





# //div[contains(@class,'srKDX')]----> with out people ask
#//div[contains(@class,'N54PNb BToiNc')] and //div[contains(@class,'srKDX')]



# //div[contains(@class,'srKDX')]//div[contains(@class,'B6fmyf byrV5b Mg1HEd')]//span[contains(@class,'VuuXrf')]----> with out people ask

# //h3[contains(@class,'LC20lb MBeuO DKV0Md')]----> this is the header
#//div[contains(@class,'B6fmyf byrV5b Mg1HEd')]//span[contains(@class,'VuuXrf')]

# full block --> //div[contains(@class,'N54PNb BToiNc')] | //div[contains(@class,'srKDX')]
#----> with out people ask
# full block with title //div[contains(@class,'N54PNb BToiNc')] | //div[contains(@class,'srKDX')]//h3[contains(@class,'LC20lb MBeuO DKV0Md')]
#full block with .com domain (//div[contains(@class,'N54PNb BToiNc')] | //div[contains(@class,'srKDX')])//div[contains(@class,'B6fmyf byrV5b Mg1HEd')]//span[contains(@class,'VuuXrf')]

#---->

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    # top=await get_google_trends()
    await init_models()
    await get_google_searched_data(search='lenevo')



if __name__ == "__main__":
    asyncio.run(main())