#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Netflix CHANGELOG 归档管理器
每月自动归档 CHANGELOG，保持主文件的可读性
"""

import os
import re
from datetime import datetime, timedelta
from typing import List, Tuple
import calendar

class NetflixChangelogArchiver:
    def __init__(self):
        self.changelog_file = "NETFLIX_CHANGELOG.md"
        self.archive_dir = "changelog_archive"
        self.header_template = """# Netflix 价格变化记录

此文件记录 Netflix 各国套餐价格的变化历史。

> 📊 **说明**：价格变化自动检测功能已启用，每次爬虫运行后都会对比上次的价格数据，生成详细的变化报告。

## 📁 历史归档

| 年月 | 归档文件 | 变化次数 |
|------|----------|----------|
{archive_links}

---

## 📅 当前月份记录

{current_month_header}
"""
    
    def ensure_archive_directory(self):
        """确保归档目录存在"""
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)
            print(f"✅ 创建归档目录: {self.archive_dir}")
    
    def parse_changelog_entries(self) -> Tuple[List[str], List[str]]:
        """解析 CHANGELOG 中的条目，分离需要归档的和保留的"""
        if not os.path.exists(self.changelog_file):
            print(f"⚠️ CHANGELOG 文件不存在: {self.changelog_file}")
            return [], []
        
        with open(self.changelog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有日期条目
        date_pattern = r'^## (\d{4}-\d{2}-\d{2})(?:\s+\d{2}:\d{2}:\d{2})?'
        
        lines = content.split('\n')
        entries_to_archive = []
        entries_to_keep = []
        current_entry = []
        current_date = None
        in_entry = False
        
        # 获取当前日期和上个月的最后一天
        now = datetime.now()
        first_day_this_month = now.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        cutoff_date = last_day_last_month.date()
        
        print(f"📅 归档截止日期: {cutoff_date.strftime('%Y-%m-%d')}")
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 检查是否是日期标题行
            match = re.match(date_pattern, line, re.MULTILINE)
            if match:
                # 保存上一个条目
                if current_entry and current_date:
                    entry_content = '\n'.join(current_entry)
                    if current_date <= cutoff_date:
                        entries_to_archive.append(entry_content)
                    else:
                        entries_to_keep.append(entry_content)
                
                # 开始新条目
                current_date = datetime.strptime(match.group(1), '%Y-%m-%d').date()
                current_entry = [line]
                in_entry = True
            elif in_entry and (line.startswith('## ') or line.startswith('# ')):
                # 遇到新的标题，结束当前条目
                if current_entry and current_date:
                    entry_content = '\n'.join(current_entry)
                    if current_date <= cutoff_date:
                        entries_to_archive.append(entry_content)
                    else:
                        entries_to_keep.append(entry_content)
                
                # 重置状态，这行不是日期条目
                current_entry = []
                current_date = None
                in_entry = False
                
                continue
            elif in_entry:
                # 添加到当前条目
                current_entry.append(line)
            
            i += 1
        
        # 处理最后一个条目
        if current_entry and current_date:
            entry_content = '\n'.join(current_entry)
            if current_date <= cutoff_date:
                entries_to_archive.append(entry_content)
            else:
                entries_to_keep.append(entry_content)
        
        return entries_to_archive, entries_to_keep
    
    def create_monthly_archive(self, entries: List[str], year_month: str) -> str:
        """创建月度归档文件"""
        if not entries:
            print(f"⚠️ {year_month} 没有需要归档的条目")
            return ""
        
        archive_filename = f"netflix_changelog_{year_month}.md"
        archive_path = os.path.join(self.archive_dir, archive_filename)
        
        # 生成归档文件内容
        year, month = year_month.split('-')
        month_name = calendar.month_name[int(month)]
        
        archive_content = f"""# Netflix 价格变化记录 - {year}年{month}月

> 📁 **归档说明**：本文件包含 {year}年{month}月 ({month_name}) 的所有价格变化记录。

## 📊 本月概览

- **记录时间范围**：{year}-{month}-01 至 {year}-{month}-{calendar.monthrange(int(year), int(month))[1]}
- **变化记录数量**：{len(entries)} 次
- **归档日期**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
        
        # 添加所有条目
        for entry in entries:
            archive_content += entry + "\n\n"
        
        # 添加页脚
        archive_content += f"""---

📚 **相关链接**：
- [返回主 CHANGELOG](../NETFLIX_CHANGELOG.md)
- [查看其他月份归档](./)

*此文件由自动归档系统生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # 写入归档文件
        with open(archive_path, 'w', encoding='utf-8') as f:
            f.write(archive_content)
        
        print(f"✅ 创建月度归档: {archive_path} ({len(entries)} 个条目)")
        return archive_filename
    
    def get_existing_archives(self) -> List[Tuple[str, str, int]]:
        """获取现有归档文件信息"""
        archives = []
        
        if not os.path.exists(self.archive_dir):
            return archives
        
        # 扫描归档目录
        for filename in os.listdir(self.archive_dir):
            if filename.startswith('netflix_changelog_') and filename.endswith('.md'):
                # 提取年月信息
                year_month = filename.replace('netflix_changelog_', '').replace('.md', '')
                if re.match(r'\d{4}-\d{2}', year_month):
                    # 统计该归档文件中的条目数量
                    archive_path = os.path.join(self.archive_dir, filename)
                    try:
                        with open(archive_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # 统计 ## YYYY-MM-DD 格式的条目
                        entry_count = len(re.findall(r'^## \d{4}-\d{2}-\d{2}', content, re.MULTILINE))
                        archives.append((year_month, filename, entry_count))
                    except Exception as e:
                        print(f"⚠️ 读取归档文件失败: {filename} - {e}")
                        archives.append((year_month, filename, 0))
        
        # 按年月排序（最新的在前）
        archives.sort(key=lambda x: x[0], reverse=True)
        return archives
    
    def generate_archive_links(self, archives: List[Tuple[str, str, int]]) -> str:
        """生成归档链接表格"""
        if not archives:
            return "| - | 暂无归档 | - |"
        
        links = []
        for year_month, filename, count in archives:
            year, month = year_month.split('-')
            month_name = calendar.month_name[int(month)]
            display_name = f"{year}年{month}月"
            link = f"| {display_name} | [netflix_changelog_{year_month}.md]({self.archive_dir}/{filename}) | {count} |"
            links.append(link)
        
        return '\n'.join(links)
    
    def update_main_changelog(self, entries_to_keep: List[str], new_archives: List[str]):
        """更新主 CHANGELOG 文件"""
        # 获取所有归档信息
        existing_archives = self.get_existing_archives()
        archive_links = self.generate_archive_links(existing_archives)
        
        # 生成当前月份标题
        now = datetime.now()
        current_month_header = f"### {now.strftime('%Y年%m月')}"
        
        # 生成新的 CHANGELOG 内容
        new_content = self.header_template.format(
            archive_links=archive_links,
            current_month_header=current_month_header
        )
        
        # 添加保留的条目
        if entries_to_keep:
            for entry in entries_to_keep:
                new_content += entry + "\n\n"
        else:
            new_content += "\n*本月暂无价格变化记录*\n\n"
        
        # 写入文件
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 更新主 CHANGELOG: {self.changelog_file}")
    
    def should_archive(self) -> bool:
        """判断是否应该执行归档（月初几天内）"""
        now = datetime.now()
        return now.day <= 3
    
    def archive_last_month(self) -> Tuple[int, List[str]]:
        """归档上个月的记录"""
        print("🗂️ 开始执行 Netflix CHANGELOG 月度归档...")
        
        # 确保归档目录存在
        self.ensure_archive_directory()
        
        # 解析现有记录
        entries_to_archive, entries_to_keep = self.parse_changelog_entries()
        
        if not entries_to_archive:
            print("📝 没有需要归档的历史记录")
            return 0, []
        
        # 按月份分组归档条目
        monthly_entries = {}
        for entry in entries_to_archive:
            # 提取日期
            match = re.search(r'^## (\d{4}-\d{2})-\d{2}', entry, re.MULTILINE)
            if match:
                year_month = match.group(1)
                if year_month not in monthly_entries:
                    monthly_entries[year_month] = []
                monthly_entries[year_month].append(entry)
        
        # 创建月度归档文件
        archived_files = []
        total_archived = 0
        
        for year_month, entries in monthly_entries.items():
            archive_filename = self.create_monthly_archive(entries, year_month)
            if archive_filename:
                archived_files.append(archive_filename)
                total_archived += len(entries)
        
        # 更新主 CHANGELOG
        self.update_main_changelog(entries_to_keep, archived_files)
        
        print(f"🎉 归档完成！共归档 {total_archived} 个条目到 {len(archived_files)} 个文件")
        return total_archived, archived_files


def main():
    """主函数"""
    archiver = NetflixChangelogArchiver()
    
    # 检查是否应该执行归档
    if not archiver.should_archive():
        now = datetime.now()
        print(f"⏰ 当前日期 {now.strftime('%Y-%m-%d')} 不在归档窗口期（每月1-3日）")
        print("跳过归档操作")
        return
    
    # 执行归档
    archived_count, archived_files = archiver.archive_last_month()
    
    # 输出结果供 GitHub Actions 使用
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        try:
            with open(github_output, 'a', encoding='utf-8') as f:
                f.write(f"archived_count={archived_count}\n")
                f.write(f"archived_files={','.join(archived_files)}\n")
            print(f"✅ GitHub Actions 输出已写入: archived_count={archived_count}")
        except Exception as e:
            print(f"⚠️ 写入 GitHub Actions 输出失败: {e}")
            # 降级到标准输出
            print(f"archived_count={archived_count}")
            print(f"archived_files={','.join(archived_files)}")
    else:
        # 如果不在 GitHub Actions 环境中，输出到标准输出
        print(f"archived_count={archived_count}")
        print(f"archived_files={','.join(archived_files)}")


if __name__ == "__main__":
    main()