# Netflix Pricing Scraper

[中文](README_zh.md) | **English**

A comprehensive tool for scraping Netflix pricing data from 190+ countries and converting prices to CNY for easy comparison.

## 🌟 Features

- **Global Coverage**: Scrapes Netflix pricing from 190+ countries worldwide
- **Smart Price Parsing**: Intelligently handles different number formats (commas, periods)
- **Currency Conversion**: Converts all prices to CNY using real-time exchange rates
- **Price Change Detection**: Tracks price changes over time with detailed changelog
- **Automated Archiving**: Organizes historical data by year/month structure
- **GitHub Actions**: Automated weekly data collection and updates

## 📊 Latest Results

The tool provides:
- **Top 10 cheapest Premium plans** ranking by CNY price
- **Complete pricing data** for all Netflix plans across all supported countries
- **Price change history** with detailed analysis
- **Archived data** for historical comparison

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for Playwright)
- OpenExchangeRates API key (free tier available)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/SzeMeng76/netflix-pricing-scraper.git
cd netflix-pricing-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
npx playwright install
```

3. Set up API key:
```bash
# Option 1: Environment variable
export API_KEY="your_openexchangerates_api_key"

# Option 2: .env file
echo "API_KEY=your_openexchangerates_api_key" > .env
```

### Usage

#### Scrape Netflix Prices
```bash
python netflix.py
```
Generates: `netflix_prices.json` and timestamped archive files

#### Convert Currencies
```bash
python netflix_rate_converter.py
```
Generates: `netflix_prices_processed.json` with CNY conversions

#### Detect Price Changes
```bash
python netflix_price_change_detector.py
```
Generates: `NETFLIX_CHANGELOG.md` and change summary files

## 📁 File Structure

```
├── netflix_prices.json                 # Latest raw pricing data
├── netflix_prices_processed.json       # Latest processed data with CNY
├── NETFLIX_CHANGELOG.md               # Price change history
├── archive/
│   └── 2025/
│       └── 08/
│           ├── netflix_prices_20250806_114340.json
│           ├── netflix_prices_processed_20250806_114340.json
│           └── netflix_price_changes_summary_20250806_114340.json
├── netflix.py                         # Main scraping script
├── netflix_rate_converter.py          # Currency conversion
├── netflix_price_change_detector.py   # Change detection
└── .github/workflows/                 # GitHub Actions automation
```

## 🔧 Configuration

### Supported Countries

The scraper supports 190+ countries including:
- **Americas**: US, Canada, Brazil, Argentina, Mexico...
- **Europe**: UK, Germany, France, Spain, Italy...
- **Asia**: Japan, Korea, India, Singapore, Thailand...
- **Africa**: Nigeria, Egypt, South Africa, Kenya...
- **Oceania**: Australia, New Zealand, Fiji...

### Price Parsing Intelligence

The tool automatically handles different number formats:
- `15,999` → 15999 (comma as thousand separator)
- `15.999` → 15999 (period as thousand separator in some regions)
- `15,99` → 15.99 (comma as decimal separator)
- `1.234,56` → 1234.56 (European format)

## 📈 Data Analysis

### Top 10 Cheapest Premium Plans (Example)

| Rank | Country | Currency | Price | CNY Equivalent |
|------|---------|----------|-------|---------------|
| 1 | Egypt | EGP 240 | 35.62 CNY |
| 2 | Nigeria | NGN 8500 | 40.00 CNY |
| 3 | India | INR 649 | 53.18 CNY |
| 4 | Argentina | ARS 15999 | 85.87 CNY |

*Data updates weekly via GitHub Actions*

## 🤖 Automation

### GitHub Actions Workflow

The project includes automated weekly data collection:
- **Schedule**: Every Sunday at 00:00 UTC
- **Process**: Scrape → Convert → Detect Changes → Archive → Commit
- **Output**: Updated JSON files, changelog, and archived historical data

### Manual Trigger
You can manually trigger the workflow from the GitHub Actions tab.

## 🛠️ Development

### Adding New Countries

1. Update `COUNTRY_INFO` in `netflix_rate_converter.py`
2. Add country code to `country_codes` list in `netflix.py`
3. Test the scraping and conversion process

### Customizing Price Detection

Modify the regex patterns in `extract_price_advanced()` function in `netflix.py` to handle new price formats.

## 📊 API Integration

### Exchange Rate API

Uses [OpenExchangeRates](https://openexchangerates.org/):
- **Free tier**: 1,000 requests/month
- **Base currency**: USD
- **Update frequency**: Real-time during conversion

## 🔍 Troubleshooting

### Common Issues

1. **Playwright browser not found**
   ```bash
   npx playwright install chromium
   ```

2. **API key not working**
   - Verify your OpenExchangeRates API key
   - Check rate limits (free tier: 1,000/month)

3. **Price parsing errors**
   - Check `COUNTRY_INFO` configuration
   - Verify Netflix page structure hasn't changed

### Debugging

Enable debug mode by setting environment variable:
```bash
export DEBUG=1
python netflix.py
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -m 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a pull request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/SzeMeng76/netflix-pricing-scraper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SzeMeng76/netflix-pricing-scraper/discussions)

## ⭐ Acknowledgments

- [Playwright](https://playwright.dev/) for web scraping
- [OpenExchangeRates](https://openexchangerates.org/) for currency conversion
- Netflix for providing pricing information

---

**Note**: This tool is for educational and research purposes only. Please respect Netflix's terms of service and rate limits.