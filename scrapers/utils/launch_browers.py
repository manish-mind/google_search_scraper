from playwright.async_api import async_playwright

DEFAULT_ARGS=[
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--hide-scrollbars",
    "--webrtc-ip-handling-policy=default_public_interface_only",
    "--force-webrtc-ip-handling-policy=default_public_interface_only",
]

async def start_browser(headless: bool = False, channel: str = "chrome", extra_args: list | None = None, proxy: dict | None = None):
    p=await async_playwright().start()
    args=DEFAULT_ARGS + (extra_args or [])

    launch_opts={
        "headless": headless,
        "channel": channel,
        "args": args,
    }

    if proxy:
        launch_opts["proxy"] = proxy

    browser = await p.chromium.launch(**launch_opts)
    return browser

async def create_context(browser, *,
                         user_agent: str | None = None,
                         viewport: dict | None = None,
                         locale: str | None = None,
                         timezone_id: str | None = None,
                         geolocation: dict | None = None,
                         permissions: list | None = None,
                         storage_state: str | None = None,
                         extra_init_scripts: list | None = None,
                         bypass_csp: bool = True):
    context_opts={
        "viewport": viewport or {"width": 1280, "height": 720},
        "user_agent": user_agent,
        "locale": locale or "en-US",
        "timezone_id": timezone_id,
        "geolocation": geolocation,
        "permissions": permissions,
        "bypass_csp": bypass_csp,
    }

    context_opts={k:v for k,v in context_opts.items() if v is not None}

    if storage_state:
        context_opts["storage_state"] = storage_state

    context=await browser.new_context(**context_opts)

    if extra_init_scripts:
        for script in extra_init_scripts:
            await context.add_init_script(script)

    if permissions and geolocation:
        # note: geolocation requires permission "geolocation"
        await context.grant_permissions(permissions, origin="https://example.com")

    return context
