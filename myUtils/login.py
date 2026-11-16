import asyncio
import sqlite3
import uuid
from pathlib import Path
from playwright.async_api import async_playwright

from conf import BASE_DIR, LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH
from myUtils.auth import check_cookie
from utils.base_social_media import set_init_script

# 统一获取浏览器启动配置（防风控+引入本地浏览器）
def get_browser_options():
    options = {
        'headless': LOCAL_CHROME_HEADLESS,
        'args': [
            '--disable-blink-features=AutomationControlled',  # 核心防爬屏蔽：去掉 window.navigator.webdriver 标签
            '--lang=zh-CN',
            '--disable-infobars',
            '--start-maximized'
        ]
    }
    # 如果用户在 conf.py 里配置了本地 Chrome，就用本地的，这样成功率极高
    if LOCAL_CHROME_PATH:
        options['executable_path'] = LOCAL_CHROME_PATH

    return options


async def _safe_close(page, context, browser):
    for resource in (page, context, browser):
        if resource is not None:
            try:
                await resource.close()
            except Exception:
                pass


def _emit_status(status_queue, value):
    if status_queue is not None:
        status_queue.put(value)


async def _complete_login(platform_type, account_id, context, status_queue):
    uuid_v1 = uuid.uuid1()
    print(f"UUID v1: {uuid_v1}")
    cookies_dir = Path(BASE_DIR / "cookiesFile")
    cookies_dir.mkdir(parents=True, exist_ok=True)
    cookie_filename = f"{uuid_v1}.json"
    await context.storage_state(path=cookies_dir / cookie_filename)
    result = await check_cookie(platform_type, cookie_filename)
    if not result:
        _emit_status(status_queue, "500")
        return False
    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_info (type, filePath, userName, status)
            VALUES (?, ?, ?, ?)
        ''', (platform_type, cookie_filename, account_id, 1))
        conn.commit()
        print("✅ 用户状态已记录")
    _emit_status(status_queue, "200")
    return True


# 抖音登录
async def douyin_cookie_gen(id, status_queue):
    url_changed_event = asyncio.Event()
    browser = context = page = None
    async with async_playwright() as playwright:
        try:
            options = get_browser_options()
            browser = await playwright.chromium.launch(**options)
            context = await browser.new_context()
            context = await set_init_script(context)
            page = await context.new_page()
            await page.goto("https://creator.douyin.com/", timeout=30000)
            original_url = page.url
            img_locator = page.get_by_role("img", name="二维码")
            await img_locator.wait_for(state="visible", timeout=20000)
            src = await img_locator.get_attribute("src")
            if not src:
                raise RuntimeError("未能获取到抖音登录二维码")
            print("✅ 图片地址:", src)
            _emit_status(status_queue, src)
            page.on(
                'framenavigated',
                lambda frame: url_changed_event.set() if frame == page.main_frame and page.url != original_url else None
            )
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)
            print("监听页面跳转成功")
            await _complete_login(3, id, context, status_queue)
        except asyncio.TimeoutError:
            print("监听页面跳转超时")
            _emit_status(status_queue, "500")
            return None
        except Exception as e:
            print(f"❌ 抖音扫码登录失败: {e}")
            _emit_status(status_queue, "500")
            return None
        finally:
            await _safe_close(page, context, browser)


# 视频号登录
async def get_tencent_cookie(id, status_queue):
    url_changed_event = asyncio.Event()
    browser = context = page = None
    async with async_playwright() as playwright:
        try:
            options = get_browser_options()
            browser = await playwright.chromium.launch(**options)
            context = await browser.new_context()
            context = await set_init_script(context)
            page = await context.new_page()
            await page.goto("https://channels.weixin.qq.com", timeout=30000)
            original_url = page.url
            page.on(
                'framenavigated',
                lambda frame: url_changed_event.set() if frame == page.main_frame and page.url != original_url else None
            )
            iframe_locator = page.frame_locator("iframe").first
            img_locator = iframe_locator.get_by_role("img").first
            await img_locator.wait_for(state="visible", timeout=20000)
            src = await img_locator.get_attribute("src")
            if not src:
                raise RuntimeError("未能获取到视频号登录二维码")
            print("✅ 图片地址:", src)
            _emit_status(status_queue, src)
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)
            print("监听页面跳转成功")
            await _complete_login(2, id, context, status_queue)
        except asyncio.TimeoutError:
            _emit_status(status_queue, "500")
            print("监听页面跳转超时")
            return None
        except Exception as e:
            print(f"❌ 视频号扫码登录失败: {e}")
            _emit_status(status_queue, "500")
            return None
        finally:
            await _safe_close(page, context, browser)


# 快手登录
async def get_ks_cookie(id, status_queue):
    url_changed_event = asyncio.Event()
    browser = context = page = None
    async with async_playwright() as playwright:
        try:
            options = get_browser_options()
            browser = await playwright.chromium.launch(**options)
            context = await browser.new_context()
            context = await set_init_script(context)
            page = await context.new_page()
            await page.goto("https://cp.kuaishou.com", timeout=30000)
            await page.get_by_role("link", name="立即登录").click(timeout=15000)
            await page.get_by_text("扫码登录").click(timeout=15000)
            img_locator = page.get_by_role("img", name="qrcode")
            await img_locator.wait_for(state="visible", timeout=20000)
            src = await img_locator.get_attribute("src")
            if not src:
                raise RuntimeError("未能获取到快手登录二维码")
            original_url = page.url
            print("✅ 图片地址:", src)
            _emit_status(status_queue, src)
            page.on(
                'framenavigated',
                lambda frame: url_changed_event.set() if frame == page.main_frame and page.url != original_url else None
            )
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)
            print("监听页面跳转成功")
            await _complete_login(4, id, context, status_queue)
        except asyncio.TimeoutError:
            _emit_status(status_queue, "500")
            print("监听页面跳转超时")
            return None
        except Exception as e:
            print(f"❌ 快手扫码登录失败: {e}")
            _emit_status(status_queue, "500")
            return None
        finally:
            await _safe_close(page, context, browser)


# 小红书登录
async def xiaohongshu_cookie_gen(id, status_queue):
    url_changed_event = asyncio.Event()
    browser = context = page = None
    async with async_playwright() as playwright:
        try:
            options = get_browser_options()
            browser = await playwright.chromium.launch(**options)
            context = await browser.new_context()
            context = await set_init_script(context)
            page = await context.new_page()
            await page.goto("https://creator.xiaohongshu.com/", timeout=30000)
            await page.locator('img.css-wemwzq').click(timeout=15000)
            img_locator = page.get_by_role("img").nth(2)
            await img_locator.wait_for(state="visible", timeout=20000)
            src = await img_locator.get_attribute("src")
            if not src:
                raise RuntimeError("未能获取到小红书登录二维码")
            original_url = page.url
            print("✅ 图片地址:", src)
            _emit_status(status_queue, src)
            page.on(
                'framenavigated',
                lambda frame: url_changed_event.set() if frame == page.main_frame and page.url != original_url else None
            )
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)
            print("监听页面跳转成功")
            await _complete_login(1, id, context, status_queue)
        except asyncio.TimeoutError:
            _emit_status(status_queue, "500")
            print("监听页面跳转超时")
            return None
        except Exception as e:
            print(f"❌ 小红书扫码登录失败: {e}")
            _emit_status(status_queue, "500")
            return None
        finally:
            await _safe_close(page, context, browser)

# a = asyncio.run(xiaohongshu_cookie_gen(4,None))
# print(a)
