#!/bin/bash

echo "测试Playwright在Docker环境中的安装..."

# 进入容器并测试Playwright
docker-compose exec backend python -c "
import asyncio
from playwright.async_api import async_playwright

async def test_playwright():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            page = await browser.new_page()
            await page.goto('https://www.google.com')
            title = await page.title()
            print(f'成功访问Google，页面标题: {title}')
            await browser.close()
            print('Playwright测试成功！')
    except Exception as e:
        print(f'Playwright测试失败: {e}')

asyncio.run(test_playwright())
"

echo "测试完成！" 