import re
import asyncio
from typing import Any
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright


def extract_price(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, 'html.parser')
    all_plans = []

    # 查找包含价格信息的段落或div
    plan_names = ['Mobile', 'Basic', 'Standard with ads', 'Standard', 'Premium']
    
    # 查找所有文本
    text_content = soup.get_text()
    
    # 支持多种价格格式的匹配模式
    price_patterns = [
        re.compile(r'\$(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*/?\s*month', re.IGNORECASE),  # $7.99/month
        re.compile(r'(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)\s*/?\s*month', re.IGNORECASE),
        re.compile(r'([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)\s*(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*/?\s*month', re.IGNORECASE)
    ]
    
    for plan_name in plan_names:
        # 查找包含计划名称的元素
        plan_elements = soup.find_all(string=re.compile(re.escape(plan_name), re.IGNORECASE))
        
        for element in plan_elements:
            # 获取包含该文本的父元素
            parent = element.parent if element.parent else element
            
            # 在父元素及其兄弟元素中查找价格
            siblings = []
            if parent and parent.parent:
                siblings = parent.parent.find_all(['p', 'div', 'span', 'td', 'th'])
            
            # 在当前元素及其后续元素中查找价格
            current_text = str(parent)
            for sibling in siblings:
                sibling_text = sibling.get_text()
                if sibling_text and len(sibling_text) < 200:  # 避免长文本
                    current_text += " " + sibling_text
            
            # 尝试所有价格模式
            price_found = False
            for price_pattern in price_patterns:
                price_matches = price_pattern.findall(current_text)
                if price_matches:
                    match = price_matches[0]
                    if isinstance(match, tuple):
                        if len(match) >= 2 and match[0].replace(',', '').replace('.', '').isdigit():
                            # 数字 货币 格式
                            price_text = f"{match[0]} {match[1]} / month"
                        else:
                            # 货币 数字 格式  
                            price_text = f"{match[1]} {match[0]} / month"
                    else:
                        # $7.99 格式
                        price_text = f"${match} / month"
                    
                    all_plans.append({
                        'plan': plan_name,
                        'price': price_text.strip()
                    })
                    price_found = True
                    break
            
            if price_found:
                break
    
    # 如果没有找到价格，尝试从整个页面文本中提取
    if not all_plans:
        all_plans = extract_from_full_text(text_content, plan_names)
    
    return all_plans


def extract_from_full_text_fallback(text_content: str, plan_names: list[str]) -> dict:
    """后备方案：从完整页面文本中提取价格信息"""
    found_plans = {}
    
    # 简化的价格模式
    price_pattern = re.compile(r'(\$?\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)?\s*/?\s*month', re.IGNORECASE)
    
    lines = text_content.split('\n')
    
    current_plan = None
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) > 100:
            continue
            
        # 检查是否包含计划名称
        for plan_name in plan_names:
            if plan_name.lower() in line.lower():
                current_plan = plan_name
                break
        
        # 如果找到了计划名称，在接下来的几行中查找价格
        if current_plan:
            for j in range(i, min(i + 8, len(lines))):
                check_line = lines[j].strip()
                price_matches = price_pattern.findall(check_line)
                if price_matches:
                    match = price_matches[0]
                    if isinstance(match, tuple) and len(match) >= 2:
                        if match[1]:  # 有货币符号
                            price_text = f"{match[0]} {match[1]} / month"
                        else:  # 没有货币符号，可能是 $7.99 格式
                            price_text = f"{match[0]} / month"
                    else:
                        price_text = f"{match} / month"
                        
                    found_plans[current_plan.lower()] = {
                        'plan': current_plan,
                        'price': price_text.strip()
                    }
                    current_plan = None
                    break
    
    return found_plans


def extract_from_full_text(text_content: str, plan_names: list[str]) -> list[dict[str, Any]]:
    """从完整页面文本中提取价格信息"""
    all_plans = []
    
    # 改进的价格模式匹配 - 支持更多格式
    price_patterns = [
        re.compile(r'(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)\s*/?\s*(month|mo)', re.IGNORECASE),
        re.compile(r'([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)\s*(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*/?\s*(month|mo)', re.IGNORECASE),
        re.compile(r'(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)', re.IGNORECASE)
    ]
    
    # 将文本按行分割
    lines = text_content.split('\n')
    
    # 扩展计划匹配模式
    plan_patterns = {
        'mobile': re.compile(r'\bmobile\b', re.IGNORECASE),
        'basic': re.compile(r'\bbasic\b', re.IGNORECASE), 
        'standard': re.compile(r'\bstandard\b', re.IGNORECASE),
        'premium': re.compile(r'\bpremium\b', re.IGNORECASE),
        'standard with ads': re.compile(r'standard.*ads|ads.*standard', re.IGNORECASE)
    }
    
    found_plans = {}
    
    # 寻找包含计划名称和价格的文本段
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) > 200:  # 跳过空行和过长行
            continue
            
        # 检查是否包含计划名称
        for plan_key, plan_pattern in plan_patterns.items():
            if plan_pattern.search(line):
                # 在当前行和附近几行中查找价格
                search_lines = lines[max(0, i-2):min(len(lines), i+5)]
                search_text = ' '.join(search_lines)
                
                # 尝试不同的价格模式
                for price_pattern in price_patterns:
                    price_matches = price_pattern.findall(search_text)
                    if price_matches:
                        # 选择第一个匹配的价格
                        match = price_matches[0]
                        if len(match) >= 2:
                            if match[0].replace(',', '').replace('.', '').isdigit():
                                # 格式: 数字 货币
                                price_text = f"{match[0]} {match[1]} / month"
                            else:
                                # 格式: 货币 数字
                                price_text = f"{match[1]} {match[0]} / month"
                            
                            plan_name = plan_key.replace('_', ' ').title()
                            if plan_name == 'Standard With Ads':
                                plan_name = 'Standard with ads'
                                
                            if plan_name not in [p['plan'] for p in found_plans.values()]:
                                found_plans[plan_key] = {
                                    'plan': plan_name,
                                    'price': price_text.strip()
                                }
                            break
    
    return list(found_plans.values())


async def fetch_netflix_prices(country_code: str) -> list[dict[str, Any]]:
    """获取特定国家的Netflix价格信息"""
    url = f'https://help.netflix.com/en/node/24926/{country_code.lower()}'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 增加页面加载时间，等待JavaScript内容
            await page.goto(url, wait_until='networkidle')
            
            # 等待页面完全加载
            await page.wait_for_timeout(3000)
            
            # 获取页面内容
            html = await page.content()
            
            # 尝试多种提取方法
            plans = extract_price_advanced(html, country_code)
            
            # 如果第一种方法没有获取到所有套餐，尝试备用方法
            if len(plans) < 3:  # 期望至少有3个套餐
                text_content = await page.inner_text('body')
                backup_plans = extract_from_page_text_detailed(text_content, country_code)
                
                # 合并结果，去重
                existing_plans = {plan['plan'] for plan in plans}
                for backup_plan in backup_plans:
                    if backup_plan['plan'] not in existing_plans:
                        plans.append(backup_plan)
            
            # 添加国家代码信息
            for plan in plans:
                plan['country_code'] = country_code.upper()
                plan['source_url'] = url
            
            return plans
            
        except Exception as e:
            print(f"获取 {country_code} 价格失败: {e}")
            return []
        finally:
            await page.close()
            await browser.close()


def extract_price_advanced(html: str, country_code: str) -> list[dict[str, Any]]:
    """高级价格提取方法"""
    soup = BeautifulSoup(html, 'html.parser')
    all_plans = []
    
    # 获取完整文本用于分析
    full_text = soup.get_text()
    
    # 定义更精确的套餐和价格模式
    plan_price_patterns = [
        # 匹配 "Standard with ads": $7.99/month 格式
        re.compile(r'["\']?(Standard\s+with\s+ads)["\']?[:\s]*\$?(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)?\s*/?\s*month', re.IGNORECASE),
        re.compile(r'["\']?(Standard)["\']?(?!\s+with\s+ads)[:\s]*\$?(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)?\s*/?\s*month', re.IGNORECASE),
        re.compile(r'["\']?(Premium)["\']?[:\s]*\$?(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)?\s*/?\s*month', re.IGNORECASE),
        re.compile(r'["\']?(Basic)["\']?[:\s]*\$?(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)?\s*/?\s*month', re.IGNORECASE),
        re.compile(r'["\']?(Mobile)["\']?[:\s]*\$?(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)?\s*/?\s*month', re.IGNORECASE),
    ]
    
    found_plans = set()
    
    # 尝试每个模式
    for pattern in plan_price_patterns:
        matches = pattern.findall(full_text)
        for match in matches:
            plan_name = match[0].strip()
            price_amount = match[1].strip()
            currency = match[2].strip() if match[2] else get_default_currency(country_code)
            
            # 格式化价格
            if currency.startswith('$') or not currency:
                currency = get_default_currency(country_code)
            
            price_text = f"{price_amount} {currency} / month"
            
            if plan_name not in found_plans:
                all_plans.append({
                    'plan': plan_name,
                    'price': price_text
                })
                found_plans.add(plan_name)
    
    return all_plans


def extract_from_page_text_detailed(text_content: str, country_code: str) -> list[dict[str, Any]]:
    """从页面文本中详细提取价格信息"""
    all_plans = []
    
    # 将文本按行分割处理
    lines = text_content.split('\n')
    
    # 更全面的套餐匹配
    plan_keywords = {
        'Standard with ads': ['standard with ads', 'standard (with ads)', 'ads standard'],
        'Premium': ['premium'],
        'Standard': ['standard'],
        'Basic': ['basic'], 
        'Mobile': ['mobile']
    }
    
    # 价格模式 - 支持多种格式
    price_patterns = [
        re.compile(r'\$(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)/month', re.IGNORECASE),
        re.compile(r'(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)\s*([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)\s*/month', re.IGNORECASE),
        re.compile(r'([A-Z]{3}|₦|USD|GBP|EUR|CAD|JPY|¥|£|€|\$|INR|₹|KRW|NGN)\s*(\d{1,3}(?:[,.]?\d{3})*(?:[.,]\d{2})?)/month', re.IGNORECASE),
    ]
    
    found_plans = {}
    
    for i, line in enumerate(lines):
        line = line.strip().lower()
        if len(line) < 3 or len(line) > 100:
            continue
            
        # 检查是否包含套餐关键词
        for plan_name, keywords in plan_keywords.items():
            for keyword in keywords:
                if keyword in line:
                    # 在当前行和后续几行中查找价格
                    search_range = lines[i:i+5]
                    search_text = ' '.join(search_range)
                    
                    # 尝试所有价格模式
                    for price_pattern in price_patterns:
                        price_matches = price_pattern.findall(search_text)
                        if price_matches:
                            match = price_matches[0]
                            
                            if isinstance(match, tuple):
                                if len(match) >= 2:
                                    # 检查哪个是数字
                                    if match[0].replace(',', '').replace('.', '').isdigit():
                                        price_text = f"{match[0]} {match[1]} / month"
                                    else:
                                        price_text = f"{match[1]} {match[0]} / month"
                                else:
                                    price_text = f"${match[0]} / month"
                            else:
                                price_text = f"${match} / month"
                            
                            if plan_name not in found_plans:
                                found_plans[plan_name] = {
                                    'plan': plan_name,
                                    'price': price_text.strip()
                                }
                            break
                    
                    if plan_name in found_plans:
                        break
            
            if plan_name in found_plans:
                break
    
    return list(found_plans.values())


def get_default_currency(country_code: str) -> str:
    """获取国家的默认货币"""
    currency_map = {
        'US': 'USD', 'CA': 'CAD', 'UK': 'GBP', 'AU': 'AUD', 'DE': 'EUR',
        'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR', 'NL': 'EUR', 'BR': 'BRL',
        'MX': 'MXN', 'AR': 'ARS', 'CL': 'CLP', 'CO': 'COP', 'PE': 'PEN',
        'JP': 'JPY', 'KR': 'KRW', 'IN': 'INR', 'NG': 'NGN', 'ZA': 'ZAR'
    }
    return currency_map.get(country_code.upper(), 'USD')


async def main():
    # 先测试主要地区的代表性国家，确保系统正常工作
    country_codes = [
        # 北美洲
        'us', 'ca', 'mx',  
        
        # 中美洲和加勒比海（大多使用USD）
        'gt', 'bz', 'sv', 'hn', 'ni', 'cr', 'pa',  # 中美洲
        'cu', 'jm', 'ht', 'do', 'tt', 'bb', 'bs',  # 加勒比海
        
        # 南美洲  
        'br', 'ar', 'cl', 'co', 've', 'uy', 'py', 'ec', 'pe', 'bo',
        
        # 欧洲
        'uk', 'de', 'fr', 'it', 'es', 'no', 'se', 'pl', 'nl', 'ch',
        
        # 亚洲
        'jp', 'kr', 'sg', 'in', 'th', 'ph', 'id', 'my', 'vn',
        'kh', 'la', 'mm', 'bt', 'mv', 'af',  # USD使用国家
        
        # 非洲
        'ng', 'za', 'ke', 'eg', 'ma', 'gh', 'tz',
        'zw', 'lr', 'sl',  # USD使用国家
        
        # 大洋洲
        'au', 'nz'
    ]
    
    results: dict[str, Any] = {}
    
    # 使用 asyncio.gather 并行处理多个请求
    tasks = []
    for country_code in country_codes:
        task = fetch_netflix_prices(country_code)
        tasks.append((country_code, task))
    
    # 控制并发数量，避免请求过多
    semaphore = asyncio.Semaphore(5)  # 最多同时5个请求
    
    async def fetch_with_semaphore(country_code: str, task):
        async with semaphore:
            plans = await task
            return country_code, plans
    
    # 执行所有任务
    completed_tasks = await asyncio.gather(*[
        fetch_with_semaphore(cc, task) 
        for cc, task in tasks
    ], return_exceptions=True)
    
    # 处理结果
    for result in completed_tasks:
        if isinstance(result, Exception):
            print(f"任务失败: {result}")
            continue
            
        country_code, plans = result
        if plans:
            results[country_code.upper()] = plans
            print(f"[{country_code.upper()}] 成功获取 {len(plans)} 个套餐")
        else:
            print(f"[{country_code.upper()}] 未获取到价格信息")
    
    return results


import json
import time
import os

if __name__ == '__main__':
    all_prices = asyncio.run(main())
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file_latest = 'netflix_prices.json'
    output_file_timestamped = f'netflix_prices_{timestamp}.json'
    
    # 保存最新版本
    with open(output_file_latest, 'w', encoding='utf-8') as f:
        json.dump(all_prices, f, ensure_ascii=False, indent=2)
    
    # 保存带时间戳的版本
    with open(output_file_timestamped, 'w', encoding='utf-8') as f:
        json.dump(all_prices, f, ensure_ascii=False, indent=2)
    
    print(f"已写入 {output_file_latest} 和 {output_file_timestamped}")
    print(f"总共获取了 {len(all_prices)} 个国家的价格信息")