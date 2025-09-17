from scrapers.utils.s3_bucket import upload_to_s3
from datetime import date,datetime
from scrapers.common.logger_config import get_logger
import base64
import aiohttp
import asyncio
import async_timeout
import os
import ssl
import certifi
from scrapers.models.google_scrap import SearchResult,ProductsOnPage,SponsoredOnPage,SearchSession
from scrapers.db.session import async_session

ssl_context = ssl.create_default_context(cafile=certifi.where())


sem = asyncio.Semaphore(10)


logger=get_logger('save_utils')

async def download_with_retry(session, url, retries=3):
    for attempt in range(retries):
        try:
            async with async_timeout.timeout(20):  # 20s per attempt
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    else:
                        logger.warning(f"[Attempt {attempt+1}] Bad status {resp.status} for {url}")
        except Exception as e:
            logger.warning(f"[Attempt {attempt+1}] Error fetching {url}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # exponential backoff
                continue
            else:
                return None
    return None


async def save_images_in_s3(img_url: str, query: str, idx: int, path:str,page_no:str,is_product:bool=False):
    async with sem:
        today = date.today().strftime("%Y-%m-%d")
        if not is_product:
            s3_key = f"{path}/{today}/{query}/{query}_{idx}.png"
        else:
            s3_key = f"{path}/{today}/{query}/page_no_{page_no}/{query}_{idx}.png"


        try:
            if img_url.startswith("data:image"):
                header, encoded = img_url.split(",", 1)
                img_bytes = base64.b64decode(encoded)
            else:
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                    img_bytes = await download_with_retry(session, img_url)

            if not img_bytes:  # <-- skip if download failed
                logger.warning(f"Skipping {img_url} → no bytes downloaded")
                return

            await upload_to_s3(img_bytes, s3_key)
            logger.info(f"Uploaded to S3: {s3_key}")

        except Exception as e:
            logger.error(f"Error saving {img_url}: {e}")


#-----> save it to local
# async def save_image_in_local(img_url: str, query: str, page_no: int, idx: int):
#     today = date.today().strftime("%Y-%m-%d")
#     folder = f"google_images/{today}/{query}/page_{page_no}"
#     os.makedirs(folder, exist_ok=True)
#     file_path = os.path.join(folder, f"{query}_{idx}.png")
#
#     try:
#         if img_url.startswith("data:image"):  # base64 case
#             header, encoded = img_url.split(",", 1)
#             img_bytes = base64.b64decode(encoded)
#             with open(file_path, "wb") as f:
#                 f.write(img_bytes)
#             logger.info(f"Saved base64: {file_path}")
#             return
#
#         async with aiohttp.ClientSession(
#             connector=aiohttp.TCPConnector(ssl=ssl_context)
#         ) as session:
#             async with session.get(img_url) as resp:
#                 if resp.status == 200:
#                     img_bytes = await resp.read()
#                     with open(file_path, "wb") as f:
#                         f.write(img_bytes)
#                     logger.info(f"Saved URL: {file_path}")
#                 else:
#                     logger.error(f"️Failed {img_url} (status {resp.status})")
#
#     except Exception as e:
#         logger.error(f"Error saving {img_url}: {e}")
#


async def save_page_screenshot_in_s3(page, query: str, path:str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    today = date.today().strftime("%Y-%m-%d")
    s3_key = f"{path}/{today}/{query}/{timestamp}.png"

    try:

        screenshot_bytes = await page.screenshot(full_page=True)

        await upload_to_s3(screenshot_bytes, s3_key)
        logger.info(f"Screenshot uploaded to S3: {s3_key}")

    except Exception as e:
        logger.error(f"Error saving screenshot for {query}: {e}")





# ----------------- DB Helpers -----------------
async def save_to_db(title, subtitle, heading, description):
    async with async_session() as session:
        new_result = SearchResult(
            title=title,
            subtitle=subtitle,
            heading=heading,
            description=description,
        )
        session.add(new_result)
        await session.commit()

def normalize_value(value: str | None):
    return None if value in (None, "N/A", "") else value


async def save_results(results: list[dict],session_id:int):
    async with async_session() as session:
        try:
            objects = [
                SearchResult(
                    title=normalize_value(r.get("title")),
                    subtitle=normalize_value(r.get("subtitle")),
                    heading=normalize_value(r.get("heading")),
                    description=normalize_value(r.get("description")),
                    is_sponsored=r.get("is_sponsored"),
                    session_id=session_id,
                    page_no=r.get("page_no")
                )
                for r in results
            ]
            session.add_all(objects)
            await session.commit()
            logger.info(f"Saved {len(objects)} results to DB")
        except Exception as e:
            await session.rollback()
            logger.error(f" Error saving results: {e}")

async def save_products_on_page(results: list[dict],session_id:int):
    async with async_session() as session:
        try:
            objects = [
                ProductsOnPage(
                    product_title=normalize_value(r.get('product_title')),
                    product_price=normalize_value(r.get('product_price')),
                    product_deliver_by=normalize_value(r.get('product_deliver_by')),
                    product_image=normalize_value(r.get('product_image')),
                    session_id=session_id
                )
                for r in results
            ]
            session.add_all(objects)
            await session.commit()
            logger.info(f"Saved {len(objects)} results to DB")
        except Exception as e:
            await session.rollback()
            logger.error(f" Error saving products on page results: {e}")

async def save_sponsored_on_page(results: list[dict],session_id:int):
    async with async_session() as session:
        try:
            objects = [
                SponsoredOnPage(
                    sponsored_title=normalize_value(r.get('sponsored_title')),
                    sponsored_subtitle=normalize_value(r.get('sponsored_subtitle')),
                    sponsored_heading=normalize_value(r.get('sponsored_heading')),
                    sponsored_description=normalize_value(r.get('sponsored_description')),
                    session_id=session_id

                )
                for r in results
            ]
            session.add_all(objects)
            await session.commit()
            logger.info(f"Saved {len(objects)} results to DB")
        except Exception as e:
            await session.rollback()
            logger.error(f" Error saving products on page results: {e}")


# ----------------- Image Saver -----------------


async def save_image(img_url: str, query: str, page_no: int, idx: int):
    today = date.today().strftime("%Y-%m-%d")
    folder = f"google_search_page_images/{today}/{query}/page_{page_no}"
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"{query}_{idx}.png")

    try:
        if img_url.startswith("data:image"):  # base64 case
            header, encoded = img_url.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            with open(file_path, "wb") as f:
                f.write(img_bytes)
            logger.info(f"Saved base64: {file_path}")
            return

        async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context)
        ) as session:
            async with session.get(img_url) as resp:
                if resp.status == 200:
                    img_bytes = await resp.read()
                    with open(file_path, "wb") as f:
                        f.write(img_bytes)
                    logger.info(f"Saved URL: {file_path}")
                else:
                    logger.error(f"️Failed {img_url} (status {resp.status})")

    except Exception as e:
        logger.error(f"Error saving {img_url}: {e}")