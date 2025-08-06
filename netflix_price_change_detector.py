#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Netflix 价格变化检测器
检测最新价格与上次价格的变化，生成changelog
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import glob

class NetflixPriceChangeDetector:
    def __init__(self):
        self.current_file = "netflix_prices.json"  # Use raw data, not processed
        self.changelog_file = "NETFLIX_CHANGELOG.md"
        
    def find_latest_archive_file(self) -> Optional[str]:
        """查找最新的归档价格文件"""
        # 查找archive目录下的所有原始价格文件
        pattern = "archive/**/netflix_prices_*.json"
        archive_files = glob.glob(pattern, recursive=True)
        
        if not archive_files:
            print("没有找到历史归档文件")
            return None
            
        # 按文件名中的时间戳排序，获取最新的
        archive_files.sort(key=lambda x: os.path.basename(x).split('_')[-1])
        latest_file = archive_files[-1]
        print(f"找到最新归档文件: {latest_file}")
        return latest_file
    
    def load_price_data(self, file_path: str) -> Dict:
        """加载价格数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"文件不存在: {file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"JSON格式错误: {file_path}")
            return {}
    
    def compare_prices(self, old_data: Dict, new_data: Dict) -> List[Dict]:
        """对比价格变化"""
        changes = []
        
        # 创建以国家-计划为key的字典，便于对比
        old_prices = {}
        new_prices = {}
        
        # 处理旧数据 - Netflix raw格式
        for country, plans in old_data.items():
            if isinstance(plans, list):
                for plan in plans:
                    if isinstance(plan, dict) and 'plan' in plan and 'price' in plan:
                        key = f"{country}_{plan['plan']}"
                        # 解析价格字符串，提取数值和货币
                        price_str = plan['price']
                        # 提取价格数值（去掉文字部分）
                        import re
                        price_match = re.search(r'([\d,\.]+)\s*([A-Z]{3}|\$|\€|\£|\¥)', price_str)
                        if price_match:
                            price_amount = price_match.group(1).replace(',', '')
                            currency = price_match.group(2)
                            old_prices[key] = {
                                'country': country,
                                'country_name': country,  # We'll use country code for now
                                'plan': plan['plan'],
                                'price_amount': price_amount,
                                'currency': currency,
                                'price_original': price_str
                            }
        
        # 处理新数据 - Netflix raw格式
        for country, plans in new_data.items():
            if isinstance(plans, list):
                for plan in plans:
                    if isinstance(plan, dict) and 'plan' in plan and 'price' in plan:
                        key = f"{country}_{plan['plan']}"
                        # 解析价格字符串，提取数值和货币
                        price_str = plan['price']
                        # 提取价格数值（去掉文字部分）
                        import re
                        price_match = re.search(r'([\d,\.]+)\s*([A-Z]{3}|\$|\€|\£|\¥)', price_str)
                        if price_match:
                            price_amount = price_match.group(1).replace(',', '')
                            currency = price_match.group(2)
                            new_prices[key] = {
                                'country': country,
                                'country_name': country,  # We'll use country code for now
                                'plan': plan['plan'],
                                'price_amount': price_amount,
                                'currency': currency,
                                'price_original': price_str
                            }
        
        # 对比价格变化
        for key, new_price in new_prices.items():
            if key in old_prices:
                old_price = old_prices[key]
                
                # 只比较相同货币的价格
                if old_price['currency'] == new_price['currency']:
                    try:
                        old_amount = float(old_price['price_amount'])
                        new_amount = float(new_price['price_amount'])
                        
                        if abs(old_amount - new_amount) > 0.01:  # 价格变化超过0.01
                            change_amount = new_amount - old_amount
                            change_percent = (change_amount / old_amount) * 100 if old_amount > 0 else 0
                            
                            changes.append({
                                'country': new_price['country'],
                                'country_name': new_price['country_name'],
                                'plan': new_price['plan'],
                                'old_price_cny': old_amount,  # Using raw amount for now
                                'new_price_cny': new_amount,
                                'change_amount': change_amount,
                                'change_percent': change_percent,
                                'price_original': new_price['price_original'],
                                'currency': new_price['currency'],
                                'type': 'price_change'
                            })
                    except (ValueError, TypeError):
                        print(f"警告：无法解析价格数据 {key}: {old_price['price_original']} -> {new_price['price_original']}")
            else:
                # 新增的套餐
                try:
                    new_amount = float(new_price['price_amount'])
                    changes.append({
                        'country': new_price['country'],
                        'country_name': new_price['country_name'],
                        'plan': new_price['plan'],
                        'new_price_cny': new_amount,  # Using raw amount for now
                        'price_original': new_price['price_original'],
                        'currency': new_price['currency'],
                        'type': 'new_plan'
                    })
                except (ValueError, TypeError):
                    print(f"警告：无法解析新套餐价格 {key}: {new_price['price_original']}")
        
        # 检查删除的套餐
        for key, old_price in old_prices.items():
            if key not in new_prices:
                try:
                    old_amount = float(old_price['price_amount'])
                    changes.append({
                        'country': old_price['country'],
                        'country_name': old_price['country_name'],
                        'plan': old_price['plan'],
                        'old_price_cny': old_amount,  # Using raw amount for now
                        'price_original': old_price['price_original'],
                        'currency': old_price['currency'],
                        'type': 'removed_plan'
                    })
                except (ValueError, TypeError):
                    print(f"警告：无法解析删除套餐价格 {key}: {old_price['price_original']}")
        
        return changes
    
    def generate_changelog_content(self, changes: List[Dict], date: str) -> str:
        """生成changelog内容"""
        if not changes:
            return f"## {date}\n\n✅ **无价格变化** - 所有套餐价格保持稳定\n\n"
        
        content = f"## {date}\n\n"
        
        # 统计变化
        price_increases = [c for c in changes if c['type'] == 'price_change' and c['change_amount'] > 0]
        price_decreases = [c for c in changes if c['type'] == 'price_change' and c['change_amount'] < 0]
        new_plans = [c for c in changes if c['type'] == 'new_plan']
        removed_plans = [c for c in changes if c['type'] == 'removed_plan']
        
        content += f"📊 **变化概览**: {len(changes)} 项变化\n"
        if price_increases:
            content += f"- 📈 涨价: {len(price_increases)} 个套餐\n"
        if price_decreases:
            content += f"- 📉 降价: {len(price_decreases)} 个套餐\n"
        if new_plans:
            content += f"- 🆕 新增: {len(new_plans)} 个套餐\n"
        if removed_plans:
            content += f"- ❌ 移除: {len(removed_plans)} 个套餐\n"
        content += "\n"
        
        # 涨价详情
        if price_increases:
            content += "### 📈 价格上涨\n\n"
            price_increases.sort(key=lambda x: x['change_percent'], reverse=True)
            for change in price_increases:
                content += f"- **{change['country_name']} ({change['country']}) - {change['plan']}**\n"
                content += f"  - 原价: ¥{change['old_price_cny']:.2f} | 现价: ¥{change['new_price_cny']:.2f}\n"
                content += f"  - 涨幅: ¥{change['change_amount']:.2f} (+{change['change_percent']:.1f}%)\n"
                content += f"  - 当地价格: {change['price_original']} {change['currency']}\n\n"
        
        # 降价详情
        if price_decreases:
            content += "### 📉 价格下降\n\n"
            price_decreases.sort(key=lambda x: x['change_percent'])
            for change in price_decreases:
                content += f"- **{change['country_name']} ({change['country']}) - {change['plan']}**\n"
                content += f"  - 原价: ¥{change['old_price_cny']:.2f} | 现价: ¥{change['new_price_cny']:.2f}\n"
                content += f"  - 降幅: ¥{abs(change['change_amount']):.2f} ({change['change_percent']:.1f}%)\n"
                content += f"  - 当地价格: {change['price_original']} {change['currency']}\n\n"
        
        # 新增套餐
        if new_plans:
            content += "### 🆕 新增套餐\n\n"
            for change in new_plans:
                content += f"- **{change['country_name']} ({change['country']}) - {change['plan']}**\n"
                content += f"  - 价格: ¥{change['new_price_cny']:.2f}\n"
                content += f"  - 当地价格: {change['price_original']} {change['currency']}\n\n"
        
        # 移除套餐
        if removed_plans:
            content += "### ❌ 移除套餐\n\n"
            for change in removed_plans:
                content += f"- **{change['country_name']} ({change['country']}) - {change['plan']}**\n"
                content += f"  - 原价格: ¥{change['old_price_cny']:.2f}\n"
                content += f"  - 当地价格: {change['price_original']} {change['currency']}\n\n"
        
        return content
    
    def update_changelog(self, new_content: str):
        """更新changelog文件"""
        if not os.path.exists(self.changelog_file):
            # 如果文件不存在，创建初始模板
            initial_content = """# Netflix 价格变化记录

此文件记录 Netflix 各国套餐价格的变化历史。

> 📊 **说明**：价格变化自动检测功能已启用，每次爬虫运行后都会对比上次的价格数据，生成详细的变化报告。

## 📁 历史归档

| 年月 | 归档文件 | 变化次数 |
|------|----------|----------|
| - | 暂无归档 | - |

---

## 📅 当前月份记录

### """ + datetime.now().strftime('%Y年%m月') + """

"""
            with open(self.changelog_file, 'w', encoding='utf-8') as f:
                f.write(initial_content + new_content + "\n")
            print(f"创建新的 Changelog: {self.changelog_file}")
            return
        
        # 读取现有内容
        with open(self.changelog_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # 查找当前月份记录的位置
        current_month = datetime.now().strftime('%Y年%m月')
        month_header_pattern = f"### {current_month}"
        
        if month_header_pattern in existing_content:
            # 在当前月份标题后插入新内容
            parts = existing_content.split(month_header_pattern, 1)
            if len(parts) == 2:
                # 查找下一个月份标题或文件结束
                after_header = parts[1]
                next_month_match = re.search(r'\n### \d{4}年\d{2}月', after_header)
                
                if next_month_match:
                    # 在下一个月份标题前插入
                    insert_pos = next_month_match.start()
                    before_next = after_header[:insert_pos]
                    after_next = after_header[insert_pos:]
                    updated_content = parts[0] + month_header_pattern + "\n\n" + new_content + before_next + after_next
                else:
                    # 在文件末尾插入
                    # 清理现有的"暂无记录"文本
                    cleaned_after = re.sub(r'\n\*本月暂无价格变化记录\*\s*', '\n', after_header)
                    updated_content = parts[0] + month_header_pattern + "\n\n" + new_content + cleaned_after
            else:
                updated_content = existing_content + "\n" + new_content
        else:
            # 添加新月份标题和内容
            updated_content = existing_content + f"\n### {current_month}\n\n" + new_content
        
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Changelog已更新: {self.changelog_file}")
    
    def generate_summary_json(self, changes: List[Dict], date: str):
        """生成变化摘要JSON文件"""
        summary = {
            'date': date,
            'timestamp': datetime.now().isoformat(),
            'total_changes': len(changes),
            'price_increases': len([c for c in changes if c['type'] == 'price_change' and c['change_amount'] > 0]),
            'price_decreases': len([c for c in changes if c['type'] == 'price_change' and c['change_amount'] < 0]),
            'new_plans': len([c for c in changes if c['type'] == 'new_plan']),
            'removed_plans': len([c for c in changes if c['type'] == 'removed_plan']),
            'changes': changes
        }
        
        # 创建归档目录并保存到archive
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        year = datetime.now().strftime('%Y')
        month = datetime.now().strftime('%m')
        archive_dir = f'archive/{year}/{month}'
        os.makedirs(archive_dir, exist_ok=True)
        
        summary_file = f"{archive_dir}/netflix_price_changes_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"变化摘要已生成: {summary_file}")
        return summary_file
    
    def detect_and_report_changes(self) -> Tuple[int, str]:
        """主函数：检测价格变化并生成报告"""
        print("开始检测 Netflix 价格变化...")
        
        # 检查当前价格文件是否存在
        if not os.path.exists(self.current_file):
            print(f"当前价格文件不存在: {self.current_file}")
            return 0, ""
        
        # 查找最新的归档文件
        latest_archive = self.find_latest_archive_file()
        if not latest_archive:
            print("没有历史数据，跳过价格对比")
            # 即使没有历史数据，也生成一个空的摘要文件
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            summary = {
                'date': date,
                'timestamp': datetime.now().isoformat(),
                'total_changes': 0,
                'price_increases': 0,
                'price_decreases': 0,
                'new_plans': 0,
                'removed_plans': 0,
                'changes': [],
                'note': '首次运行或无历史数据，跳过价格对比'
            }
            # 创建归档目录并保存到archive
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            year = datetime.now().strftime('%Y')
            month = datetime.now().strftime('%m')
            archive_dir = f'archive/{year}/{month}'
            os.makedirs(archive_dir, exist_ok=True)
            
            summary_file = f"{archive_dir}/netflix_price_changes_summary_{timestamp}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(f"生成初始摘要文件: {summary_file}")
            return 0, summary_file
        
        # 加载数据
        old_data = self.load_price_data(latest_archive)
        new_data = self.load_price_data(self.current_file)
        
        if not old_data or not new_data:
            print("数据加载失败")
            return 0, ""
        
        # 对比价格
        changes = self.compare_prices(old_data, new_data)
        
        # 生成报告
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        changelog_content = self.generate_changelog_content(changes, date)
        
        # 更新changelog
        self.update_changelog(changelog_content)
        
        # 生成摘要JSON
        summary_file = self.generate_summary_json(changes, date)
        
        print(f"Netflix 价格变化检测完成，发现 {len(changes)} 项变化")
        return len(changes), summary_file


if __name__ == "__main__":
    detector = NetflixPriceChangeDetector()
    changes_count, summary_file = detector.detect_and_report_changes()
    
    # 检查是否需要执行 CHANGELOG 归档
    now = datetime.now()
    if now.day <= 3:  # 每月前3天检查归档
        print("\n检查 CHANGELOG 归档需求...")
        try:
            import subprocess
            import sys
            
            # 使用当前 Python 解释器来运行归档脚本
            result = subprocess.run([sys.executable, 'netflix_changelog_archiver.py'], 
                                  capture_output=True, text=True, encoding='utf-8')
            if result.returncode == 0:
                print("CHANGELOG 归档检查完成")
                if result.stdout.strip():
                    print(result.stdout.strip())
            else:
                print(f"CHANGELOG 归档失败: {result.stderr}")
        except Exception as e:
            print(f"执行 CHANGELOG 归档时出错: {e}")
    
    # 输出结果供GitHub Actions使用
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output and github_output != '/dev/stdout':
        with open(github_output, 'a') as f:
            f.write(f"changes_count={changes_count}\n")
            f.write(f"summary_file={summary_file}\n")
    else:
        # 如果不在 GitHub Actions 环境中，输出到标准输出
        print(f"changes_count={changes_count}")
        print(f"summary_file={summary_file}")