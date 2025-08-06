# Netflix 价格爬虫

**中文** | [English](README.md)

一个全面的工具，用于从190+个国家抓取Netflix定价数据，并转换为人民币进行便捷比较。

## 🌟 特性

- **全球覆盖**: 抓取全球190+个国家的Netflix定价
- **智能价格解析**: 智能处理不同数字格式（逗号、句号分隔符）
- **货币转换**: 使用实时汇率将所有价格转换为人民币
- **价格变化检测**: 跟踪价格变化，生成详细变更日志
- **自动归档**: 按年/月结构组织历史数据
- **GitHub Actions**: 自动化每周数据收集和更新

## 📊 最新结果

工具提供：
- **最便宜的10个Premium套餐**按人民币价格排序
- **完整定价数据**涵盖所有支持国家的所有Netflix套餐
- **价格变化历史**包含详细分析
- **归档数据**用于历史对比

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Node.js 18+ (用于 Playwright)
- OpenExchangeRates API密钥 (有免费层级)

### 安装

1. 克隆仓库:
```bash
git clone https://github.com/SzeMeng76/netflix-pricing-scraper.git
cd netflix-pricing-scraper
```

2. 安装依赖:
```bash
pip install -r requirements.txt
npx playwright install
```

3. 设置API密钥:
```bash
# 方式1: 环境变量
export API_KEY="your_openexchangerates_api_key"

# 方式2: .env文件
echo "API_KEY=your_openexchangerates_api_key" > .env
```

### 使用方法

#### 抓取Netflix价格
```bash
python netflix.py
```
生成: `netflix_prices.json` 和带时间戳的归档文件

#### 转换货币
```bash
python netflix_rate_converter.py
```
生成: `netflix_prices_processed.json` 包含人民币转换

#### 检测价格变化
```bash
python netflix_price_change_detector.py
```
生成: `NETFLIX_CHANGELOG.md` 和变化摘要文件

## 📁 文件结构

```
├── netflix_prices.json                 # 最新原始定价数据
├── netflix_prices_processed.json       # 最新处理数据（含人民币）
├── NETFLIX_CHANGELOG.md               # 价格变化历史
├── archive/
│   └── 2025/
│       └── 08/
│           ├── netflix_prices_20250806_114340.json
│           ├── netflix_prices_processed_20250806_114340.json
│           └── netflix_price_changes_summary_20250806_114340.json
├── netflix.py                         # 主要爬虫脚本
├── netflix_rate_converter.py          # 货币转换
├── netflix_price_change_detector.py   # 变化检测
└── .github/workflows/                 # GitHub Actions 自动化
```

## 🔧 配置

### 支持的国家

爬虫支持190+个国家，包括：
- **美洲**: 美国、加拿大、巴西、阿根廷、墨西哥...
- **欧洲**: 英国、德国、法国、西班牙、意大利...
- **亚洲**: 日本、韩国、印度、新加坡、泰国...
- **非洲**: 尼日利亚、埃及、南非、肯尼亚...
- **大洋洲**: 澳大利亚、新西兰、斐济...

### 智能价格解析

工具自动处理不同数字格式：
- `15,999` → 15999 (逗号作为千位分隔符)
- `15.999` → 15999 (句号作为千位分隔符，某些地区)
- `15,99` → 15.99 (逗号作为小数分隔符)
- `1.234,56` → 1234.56 (欧洲格式)

## 📈 数据分析

### 最便宜的10个Premium套餐 (示例)

| 排名 | 国家 | 货币 | 价格 | 人民币等值 |
|------|------|------|------|----------|
| 1 | 埃及 | EGP 240 | 35.62 CNY |
| 2 | 尼日利亚 | NGN 8500 | 40.00 CNY |
| 3 | 印度 | INR 649 | 53.18 CNY |
| 4 | 阿根廷 | ARS 15999 | 85.87 CNY |

*数据通过GitHub Actions每周更新*

## 🤖 自动化

### GitHub Actions 工作流

项目包含自动化每周数据收集：
- **时间安排**: 每周日UTC时间00:00
- **流程**: 爬取 → 转换 → 检测变化 → 归档 → 提交
- **输出**: 更新的JSON文件、变更日志和归档的历史数据

### 手动触发
您可以从GitHub Actions标签页手动触发工作流。

## 🛠️ 开发

### 添加新国家

1. 在 `netflix_rate_converter.py` 中更新 `COUNTRY_INFO`
2. 在 `netflix.py` 的 `country_codes` 列表中添加国家代码
3. 测试爬取和转换过程

### 自定义价格检测

修改 `netflix.py` 中 `extract_price_advanced()` 函数的正则表达式模式来处理新的价格格式。

## 📊 API集成

### 汇率API

使用 [OpenExchangeRates](https://openexchangerates.org/):
- **免费层级**: 每月1,000次请求
- **基础货币**: USD
- **更新频率**: 转换时实时更新

## 🔍 故障排除

### 常见问题

1. **Playwright浏览器未找到**
   ```bash
   npx playwright install chromium
   ```

2. **API密钥不工作**
   - 验证您的OpenExchangeRates API密钥
   - 检查速率限制（免费层级：1,000/月）

3. **价格解析错误**
   - 检查 `COUNTRY_INFO` 配置
   - 验证Netflix页面结构是否发生变化

### 调试

通过设置环境变量启用调试模式：
```bash
export DEBUG=1
python netflix.py
```

## 📄 许可证

MIT许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

1. Fork 仓库
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -m 'Add new feature'`
4. 推送到分支: `git push origin feature/new-feature`
5. 提交拉取请求

## 📞 支持

- **问题**: [GitHub Issues](https://github.com/SzeMeng76/netflix-pricing-scraper/issues)
- **讨论**: [GitHub Discussions](https://github.com/SzeMeng76/netflix-pricing-scraper/discussions)

## ⭐ 致谢

- [Playwright](https://playwright.dev/) 提供网页爬取功能
- [OpenExchangeRates](https://openexchangerates.org/) 提供货币转换
- Netflix 提供定价信息

---

**注意**: 此工具仅用于教育和研究目的。请尊重Netflix的服务条款和速率限制。