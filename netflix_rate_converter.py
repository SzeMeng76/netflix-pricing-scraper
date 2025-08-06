import json
import requests
import re
import time
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

import os

# --- Configuration ---

# 尝试加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv 不是必需的依赖
    pass

# 从环境变量获取API密钥，如果没有则使用默认值（仅用于本地测试）
API_KEYS = []

# 读取API密钥
api_key = os.getenv('API_KEY')
if api_key:
    API_KEYS.append(api_key)

# 如果没有环境变量，使用默认密钥（仅用于本地开发测试）
if not API_KEYS:
    # 临时使用提供的API密钥
    API_KEYS.append("daaf8da9e5fd46bd95bb8f20f4cf1309")
API_URL_TEMPLATE = "https://openexchangerates.org/api/latest.json?app_id={}"
INPUT_JSON_PATH = 'netflix_prices.json' # Input JSON file path
OUTPUT_JSON_PATH = 'netflix_prices_processed.json' # New output file path

# Static Country Information - 扩展到所有Netflix支持的国家
COUNTRY_INFO = {
    # 北美洲
    "US": {"name_en": "United States", "name_cn": "美国", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "CA": {"name_en": "Canada", "name_cn": "加拿大", "currency": "CAD", "symbol": "CA$", "decimal": ".", "thousand": ","},
    "MX": {"name_en": "Mexico", "name_cn": "墨西哥", "currency": "MXN", "symbol": "MX$", "decimal": ".", "thousand": ","},
    "GT": {"name_en": "Guatemala", "name_cn": "危地马拉", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "BZ": {"name_en": "Belize", "name_cn": "伯利兹", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "SV": {"name_en": "El Salvador", "name_cn": "萨尔瓦多", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "HN": {"name_en": "Honduras", "name_cn": "洪都拉斯", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "NI": {"name_en": "Nicaragua", "name_cn": "尼加拉瓜", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "CR": {"name_en": "Costa Rica", "name_cn": "哥斯达黎加", "currency": "CRC", "symbol": "₡", "decimal": ".", "thousand": ","},
    "PA": {"name_en": "Panama", "name_cn": "巴拿马", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    
    # 加勒比海
    "CU": {"name_en": "Cuba", "name_cn": "古巴", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "DO": {"name_en": "Dominican Republic", "name_cn": "多米尼加", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "HT": {"name_en": "Haiti", "name_cn": "海地", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "JM": {"name_en": "Jamaica", "name_cn": "牙买加", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "TT": {"name_en": "Trinidad and Tobago", "name_cn": "特立尼达和多巴哥", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "BB": {"name_en": "Barbados", "name_cn": "巴巴多斯", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "BS": {"name_en": "Bahamas", "name_cn": "巴哈马", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    
    # 南美洲
    "BR": {"name_en": "Brazil", "name_cn": "巴西", "currency": "BRL", "symbol": "R$", "decimal": ",", "thousand": "."},
    "AR": {"name_en": "Argentina", "name_cn": "阿根廷", "currency": "ARS", "symbol": "ARS", "decimal": ",", "thousand": "."},
    "CL": {"name_en": "Chile", "name_cn": "智利", "currency": "CLP", "symbol": "CLP", "decimal": ".", "thousand": ","},
    "CO": {"name_en": "Colombia", "name_cn": "哥伦比亚", "currency": "COP", "symbol": "COP", "decimal": ".", "thousand": ","},
    "VE": {"name_en": "Venezuela", "name_cn": "委内瑞拉", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "PE": {"name_en": "Peru", "name_cn": "秘鲁", "currency": "PEN", "symbol": "PEN", "decimal": ".", "thousand": ","},
    "EC": {"name_en": "Ecuador", "name_cn": "厄瓜多尔", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "BO": {"name_en": "Bolivia", "name_cn": "玻利维亚", "currency": "BOB", "symbol": "Bs", "decimal": ".", "thousand": ","},
    "UY": {"name_en": "Uruguay", "name_cn": "乌拉圭", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "PY": {"name_en": "Paraguay", "name_cn": "巴拉圭", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "GY": {"name_en": "Guyana", "name_cn": "圭亚那", "currency": "GYD", "symbol": "G$", "decimal": ".", "thousand": ","},
    "SR": {"name_en": "Suriname", "name_cn": "苏里南", "currency": "SRD", "symbol": "$", "decimal": ",", "thousand": "."},
    
    # 西欧
    "UK": {"name_en": "United Kingdom", "name_cn": "英国", "currency": "GBP", "symbol": "£", "decimal": ".", "thousand": ","},
    "GB": {"name_en": "United Kingdom", "name_cn": "英国", "currency": "GBP", "symbol": "£", "decimal": ".", "thousand": ","},
    "IE": {"name_en": "Ireland", "name_cn": "爱尔兰", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "FR": {"name_en": "France", "name_cn": "法国", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "DE": {"name_en": "Germany", "name_cn": "德国", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "IT": {"name_en": "Italy", "name_cn": "意大利", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "ES": {"name_en": "Spain", "name_cn": "西班牙", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "PT": {"name_en": "Portugal", "name_cn": "葡萄牙", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "NL": {"name_en": "Netherlands", "name_cn": "荷兰", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "BE": {"name_en": "Belgium", "name_cn": "比利时", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "LU": {"name_en": "Luxembourg", "name_cn": "卢森堡", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "AT": {"name_en": "Austria", "name_cn": "奥地利", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "CH": {"name_en": "Switzerland", "name_cn": "瑞士", "currency": "CHF", "symbol": "CHF", "decimal": ".", "thousand": ","},
    
    # 北欧
    "IS": {"name_en": "Iceland", "name_cn": "冰岛", "currency": "ISK", "symbol": "kr", "decimal": ".", "thousand": ","},
    "NO": {"name_en": "Norway", "name_cn": "挪威", "currency": "NOK", "symbol": "kr", "decimal": ".", "thousand": ","},
    "SE": {"name_en": "Sweden", "name_cn": "瑞典", "currency": "SEK", "symbol": "kr", "decimal": ".", "thousand": ","},
    "FI": {"name_en": "Finland", "name_cn": "芬兰", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "DK": {"name_en": "Denmark", "name_cn": "丹麦", "currency": "DKK", "symbol": "kr", "decimal": ".", "thousand": ","},
    
    # 东欧
    "PL": {"name_en": "Poland", "name_cn": "波兰", "currency": "PLN", "symbol": "zł", "decimal": ".", "thousand": ","},
    "CZ": {"name_en": "Czech Republic", "name_cn": "捷克", "currency": "CZK", "symbol": "Kč", "decimal": ".", "thousand": ","},
    "SK": {"name_en": "Slovakia", "name_cn": "斯洛伐克", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "HU": {"name_en": "Hungary", "name_cn": "匈牙利", "currency": "HUF", "symbol": "Ft", "decimal": ".", "thousand": ","},
    "RO": {"name_en": "Romania", "name_cn": "罗马尼亚", "currency": "RON", "symbol": "lei", "decimal": ".", "thousand": ","},
    "BG": {"name_en": "Bulgaria", "name_cn": "保加利亚", "currency": "BGN", "symbol": "лв", "decimal": ".", "thousand": ","},
    "HR": {"name_en": "Croatia", "name_cn": "克罗地亚", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "SI": {"name_en": "Slovenia", "name_cn": "斯洛文尼亚", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "EE": {"name_en": "Estonia", "name_cn": "爱沙尼亚", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "LV": {"name_en": "Latvia", "name_cn": "拉脱维亚", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "LT": {"name_en": "Lithuania", "name_cn": "立陶宛", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    
    # 东亚
    "JP": {"name_en": "Japan", "name_cn": "日本", "currency": "JPY", "symbol": "¥", "decimal": ".", "thousand": ","},
    "KR": {"name_en": "South Korea", "name_cn": "韩国", "currency": "KRW", "symbol": "₩", "decimal": ".", "thousand": ","},
    "CN": {"name_en": "China", "name_cn": "中国", "currency": "CNY", "symbol": "¥", "decimal": ".", "thousand": ","},
    "HK": {"name_en": "Hong Kong", "name_cn": "香港", "currency": "HKD", "symbol": "HK$", "decimal": ".", "thousand": ","},
    "TW": {"name_en": "Taiwan", "name_cn": "台湾", "currency": "TWD", "symbol": "NT$", "decimal": ".", "thousand": ","},
    
    # 东南亚
    "SG": {"name_en": "Singapore", "name_cn": "新加坡", "currency": "SGD", "symbol": "S$", "decimal": ".", "thousand": ","},
    "MY": {"name_en": "Malaysia", "name_cn": "马来西亚", "currency": "MYR", "symbol": "RM", "decimal": ".", "thousand": ","},
    "TH": {"name_en": "Thailand", "name_cn": "泰国", "currency": "THB", "symbol": "฿", "decimal": ".", "thousand": ","},
    "VN": {"name_en": "Vietnam", "name_cn": "越南", "currency": "VND", "symbol": "₫", "decimal": ".", "thousand": ","},
    "PH": {"name_en": "Philippines", "name_cn": "菲律宾", "currency": "PHP", "symbol": "₱", "decimal": ".", "thousand": ","},
    "ID": {"name_en": "Indonesia", "name_cn": "印度尼西亚", "currency": "IDR", "symbol": "Rp", "decimal": ".", "thousand": ","},
    "KH": {"name_en": "Cambodia", "name_cn": "柬埔寨", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "LA": {"name_en": "Laos", "name_cn": "老挝", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "MM": {"name_en": "Myanmar", "name_cn": "缅甸", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "BN": {"name_en": "Brunei", "name_cn": "文莱", "currency": "BND", "symbol": "B$", "decimal": ".", "thousand": ","},
    
    # 南亚
    "IN": {"name_en": "India", "name_cn": "印度", "currency": "INR", "symbol": "₹", "decimal": ".", "thousand": ","},
    "PK": {"name_en": "Pakistan", "name_cn": "巴基斯坦", "currency": "PKR", "symbol": "Rs", "decimal": ".", "thousand": ","},
    "BD": {"name_en": "Bangladesh", "name_cn": "孟加拉国", "currency": "BDT", "symbol": "৳", "decimal": ".", "thousand": ","},
    "LK": {"name_en": "Sri Lanka", "name_cn": "斯里兰卡", "currency": "LKR", "symbol": "Rs", "decimal": ".", "thousand": ","},
    "NP": {"name_en": "Nepal", "name_cn": "尼泊尔", "currency": "NPR", "symbol": "Rs", "decimal": ".", "thousand": ","},
    "BT": {"name_en": "Bhutan", "name_cn": "不丹", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "MV": {"name_en": "Maldives", "name_cn": "马尔代夫", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    
    # 中东
    "TR": {"name_en": "Turkey", "name_cn": "土耳其", "currency": "TRY", "symbol": "₺", "decimal": ".", "thousand": ","},
    "SA": {"name_en": "Saudi Arabia", "name_cn": "沙特阿拉伯", "currency": "SAR", "symbol": "﷼", "decimal": ".", "thousand": ","},
    "AE": {"name_en": "UAE", "name_cn": "阿联酋", "currency": "AED", "symbol": "د.إ", "decimal": ".", "thousand": ","},
    "IL": {"name_en": "Israel", "name_cn": "以色列", "currency": "ILS", "symbol": "₪", "decimal": ".", "thousand": ","},
    
    # 非洲
    "NG": {"name_en": "Nigeria", "name_cn": "尼日利亚", "currency": "NGN", "symbol": "₦", "decimal": ".", "thousand": ","},
    "ZA": {"name_en": "South Africa", "name_cn": "南非", "currency": "ZAR", "symbol": "R", "decimal": ".", "thousand": ","},
    "KE": {"name_en": "Kenya", "name_cn": "肯尼亚", "currency": "KES", "symbol": "KSh", "decimal": ".", "thousand": ","},
    "EG": {"name_en": "Egypt", "name_cn": "埃及", "currency": "EGP", "symbol": "£", "decimal": ".", "thousand": ","},
    "MA": {"name_en": "Morocco", "name_cn": "摩洛哥", "currency": "MAD", "symbol": "د.م.", "decimal": ".", "thousand": ","},
    "TN": {"name_en": "Tunisia", "name_cn": "突尼斯", "currency": "TND", "symbol": "د.ت", "decimal": ".", "thousand": ","},
    "GH": {"name_en": "Ghana", "name_cn": "加纳", "currency": "GHS", "symbol": "₵", "decimal": ".", "thousand": ","},
    "TZ": {"name_en": "Tanzania", "name_cn": "坦桑尼亚", "currency": "TZS", "symbol": "TSh", "decimal": ".", "thousand": ","},
    "UG": {"name_en": "Uganda", "name_cn": "乌干达", "currency": "UGX", "symbol": "USh", "decimal": ".", "thousand": ","},
    "ZM": {"name_en": "Zambia", "name_cn": "赞比亚", "currency": "ZMW", "symbol": "ZK", "decimal": ".", "thousand": ","},
    "MZ": {"name_en": "Mozambique", "name_cn": "莫桑比克", "currency": "MZN", "symbol": "MT", "decimal": ".", "thousand": ","},
    "ZW": {"name_en": "Zimbabwe", "name_cn": "津巴布韦", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "LR": {"name_en": "Liberia", "name_cn": "利比里亚", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "SL": {"name_en": "Sierra Leone", "name_cn": "塞拉利昂", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    
    # 中东/中亚
    "AF": {"name_en": "Afghanistan", "name_cn": "阿富汗", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    
    # 巴尔干半岛和前南斯拉夫地区
    "RS": {"name_en": "Serbia", "name_cn": "塞尔维亚", "currency": "RSD", "symbol": "din", "decimal": ",", "thousand": "."},
    "ME": {"name_en": "Montenegro", "name_cn": "黑山", "currency": "EUR", "symbol": "€", "decimal": ",", "thousand": "."},
    "BA": {"name_en": "Bosnia and Herzegovina", "name_cn": "波斯尼亚和黑塞哥维那", "currency": "BAM", "symbol": "КМ", "decimal": ",", "thousand": "."},
    "MK": {"name_en": "North Macedonia", "name_cn": "北马其顿", "currency": "MKD", "symbol": "ден", "decimal": ",", "thousand": "."},
    "AL": {"name_en": "Albania", "name_cn": "阿尔巴尼亚", "currency": "ALL", "symbol": "L", "decimal": ",", "thousand": "."},
    
    # 东欧/前苏联地区
    "UA": {"name_en": "Ukraine", "name_cn": "乌克兰", "currency": "UAH", "symbol": "₴", "decimal": ",", "thousand": " "},
    "BY": {"name_en": "Belarus", "name_cn": "白俄罗斯", "currency": "BYN", "symbol": "Br", "decimal": ",", "thousand": " "},
    "MD": {"name_en": "Moldova", "name_cn": "摩尔多瓦", "currency": "MDL", "symbol": "L", "decimal": ",", "thousand": " "},
    
    # 高加索地区
    "GE": {"name_en": "Georgia", "name_cn": "格鲁吉亚", "currency": "GEL", "symbol": "₾", "decimal": ".", "thousand": ","},
    "AM": {"name_en": "Armenia", "name_cn": "亚美尼亚", "currency": "AMD", "symbol": "֏", "decimal": ".", "thousand": ","},
    "AZ": {"name_en": "Azerbaijan", "name_cn": "阿塞拜疆", "currency": "AZN", "symbol": "₼", "decimal": ".", "thousand": ","},
    
    # 中亚地区
    "KZ": {"name_en": "Kazakhstan", "name_cn": "哈萨克斯坦", "currency": "KZT", "symbol": "₸", "decimal": ",", "thousand": " "},
    "KG": {"name_en": "Kyrgyzstan", "name_cn": "吉尔吉斯斯坦", "currency": "KGS", "symbol": "с", "decimal": ",", "thousand": " "},
    "TJ": {"name_en": "Tajikistan", "name_cn": "塔吉克斯坦", "currency": "TJS", "symbol": "ЅМ", "decimal": ".", "thousand": ","},
    "TM": {"name_en": "Turkmenistan", "name_cn": "土库曼斯坦", "currency": "TMT", "symbol": "T", "decimal": ".", "thousand": ","},
    "UZ": {"name_en": "Uzbekistan", "name_cn": "乌兹别克斯坦", "currency": "UZS", "symbol": "soʻm", "decimal": ",", "thousand": " "},
    
    # 中东地区（补充）
    "QA": {"name_en": "Qatar", "name_cn": "卡塔尔", "currency": "QAR", "symbol": "﷼", "decimal": ".", "thousand": ","},
    "KW": {"name_en": "Kuwait", "name_cn": "科威特", "currency": "KWD", "symbol": "د.ك", "decimal": ".", "thousand": ","},
    "BH": {"name_en": "Bahrain", "name_cn": "巴林", "currency": "BHD", "symbol": "د.ب", "decimal": ".", "thousand": ","},
    "OM": {"name_en": "Oman", "name_cn": "阿曼", "currency": "OMR", "symbol": "﷼", "decimal": ".", "thousand": ","},
    "JO": {"name_en": "Jordan", "name_cn": "约旦", "currency": "JOD", "symbol": "د.ا", "decimal": ".", "thousand": ","},
    "LB": {"name_en": "Lebanon", "name_cn": "黎巴嫩", "currency": "LBP", "symbol": "ل.ل", "decimal": ".", "thousand": ","},
    "IQ": {"name_en": "Iraq", "name_cn": "伊拉克", "currency": "IQD", "symbol": "د.ع", "decimal": ".", "thousand": ","},
    "YE": {"name_en": "Yemen", "name_cn": "也门", "currency": "YER", "symbol": "﷼", "decimal": ".", "thousand": ","},
    "PS": {"name_en": "Palestine", "name_cn": "巴勒斯坦", "currency": "ILS", "symbol": "₪", "decimal": ".", "thousand": ","},
    "CY": {"name_en": "Cyprus", "name_cn": "塞浦路斯", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "LY": {"name_en": "Libya", "name_cn": "利比亚", "currency": "LYD", "symbol": "د.ل", "decimal": ".", "thousand": ","},
    
    # 北非地区（补充）
    "DZ": {"name_en": "Algeria", "name_cn": "阿尔及利亚", "currency": "DZD", "symbol": "د.ج", "decimal": ".", "thousand": ","},
    "SD": {"name_en": "Sudan", "name_cn": "苏丹", "currency": "SDG", "symbol": "ج.س", "decimal": ".", "thousand": ","},
    "EH": {"name_en": "Western Sahara", "name_cn": "西撒哈拉", "currency": "MAD", "symbol": "د.م.", "decimal": ".", "thousand": ","},
    
    # 西非地区（补充）
    "SN": {"name_en": "Senegal", "name_cn": "塞内加尔", "currency": "XOF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "ML": {"name_en": "Mali", "name_cn": "马里", "currency": "XOF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "BF": {"name_en": "Burkina Faso", "name_cn": "布基纳法索", "currency": "XOF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "NE": {"name_en": "Niger", "name_cn": "尼日尔", "currency": "XOF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "GN": {"name_en": "Guinea", "name_cn": "几内亚", "currency": "GNF", "symbol": "FG", "decimal": ".", "thousand": ","},
    "CI": {"name_en": "Ivory Coast", "name_cn": "科特迪瓦", "currency": "XOF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "GM": {"name_en": "Gambia", "name_cn": "冈比亚", "currency": "GMD", "symbol": "D", "decimal": ".", "thousand": ","},
    "GW": {"name_en": "Guinea-Bissau", "name_cn": "几内亚比绍", "currency": "XOF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "CV": {"name_en": "Cape Verde", "name_cn": "佛得角", "currency": "CVE", "symbol": "$", "decimal": ".", "thousand": ","},
    "MR": {"name_en": "Mauritania", "name_cn": "毛里塔尼亚", "currency": "MRU", "symbol": "UM", "decimal": ".", "thousand": ","},
    "TG": {"name_en": "Togo", "name_cn": "多哥", "currency": "XOF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "BJ": {"name_en": "Benin", "name_cn": "贝宁", "currency": "XOF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    
    # 中非地区（补充）
    "CD": {"name_en": "Democratic Republic of the Congo", "name_cn": "刚果民主共和国", "currency": "CDF", "symbol": "FC", "decimal": ".", "thousand": ","},
    "CG": {"name_en": "Republic of the Congo", "name_cn": "刚果共和国", "currency": "XAF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "CF": {"name_en": "Central African Republic", "name_cn": "中非共和国", "currency": "XAF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "CM": {"name_en": "Cameroon", "name_cn": "喀麦隆", "currency": "XAF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "TD": {"name_en": "Chad", "name_cn": "乍得", "currency": "XAF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "GQ": {"name_en": "Equatorial Guinea", "name_cn": "赤道几内亚", "currency": "XAF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "GA": {"name_en": "Gabon", "name_cn": "加蓬", "currency": "XAF", "symbol": "CFA", "decimal": ".", "thousand": ","},
    "ST": {"name_en": "Sao Tome and Principe", "name_cn": "圣多美和普林西比", "currency": "STN", "symbol": "Db", "decimal": ".", "thousand": ","},
    "AO": {"name_en": "Angola", "name_cn": "安哥拉", "currency": "AOA", "symbol": "Kz", "decimal": ".", "thousand": ","},
    
    # 东非地区（补充）
    "ET": {"name_en": "Ethiopia", "name_cn": "埃塞俄比亚", "currency": "ETB", "symbol": "Br", "decimal": ".", "thousand": ","},
    "RW": {"name_en": "Rwanda", "name_cn": "卢旺达", "currency": "RWF", "symbol": "FRw", "decimal": ".", "thousand": ","},
    "BI": {"name_en": "Burundi", "name_cn": "布隆迪", "currency": "BIF", "symbol": "FBu", "decimal": ".", "thousand": ","},
    "SO": {"name_en": "Somalia", "name_cn": "索马里", "currency": "SOS", "symbol": "S", "decimal": ".", "thousand": ","},
    "DJ": {"name_en": "Djibouti", "name_cn": "吉布提", "currency": "DJF", "symbol": "Fdj", "decimal": ".", "thousand": ","},
    "ER": {"name_en": "Eritrea", "name_cn": "厄立特里亚", "currency": "ERN", "symbol": "Nfk", "decimal": ".", "thousand": ","},
    "SS": {"name_en": "South Sudan", "name_cn": "南苏丹", "currency": "SSP", "symbol": "£", "decimal": ".", "thousand": ","},
    
    # 印度洋地区（补充）
    "MG": {"name_en": "Madagascar", "name_cn": "马达加斯加", "currency": "MGA", "symbol": "Ar", "decimal": ".", "thousand": ","},
    "MU": {"name_en": "Mauritius", "name_cn": "毛里求斯", "currency": "MUR", "symbol": "₨", "decimal": ".", "thousand": ","},
    "SC": {"name_en": "Seychelles", "name_cn": "塞舌尔", "currency": "SCR", "symbol": "₨", "decimal": ".", "thousand": ","},
    "KM": {"name_en": "Comoros", "name_cn": "科摩罗", "currency": "KMF", "symbol": "CF", "decimal": ".", "thousand": ","},
    "YT": {"name_en": "Mayotte", "name_cn": "马约特", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "RE": {"name_en": "Reunion", "name_cn": "留尼汪", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    
    # 大洋洲
    "AU": {"name_en": "Australia", "name_cn": "澳大利亚", "currency": "AUD", "symbol": "A$", "decimal": ".", "thousand": ","},
    "NZ": {"name_en": "New Zealand", "name_cn": "新西兰", "currency": "NZD", "symbol": "NZ$", "decimal": ".", "thousand": ","},
    "FJ": {"name_en": "Fiji", "name_cn": "斐济", "currency": "FJD", "symbol": "FJ$", "decimal": ".", "thousand": ","},
    "PG": {"name_en": "Papua New Guinea", "name_cn": "巴布亚新几内亚", "currency": "PGK", "symbol": "K", "decimal": ".", "thousand": ","},
    
    # 太平洋岛国（补充）
    "SB": {"name_en": "Solomon Islands", "name_cn": "所罗门群岛", "currency": "SBD", "symbol": "$", "decimal": ".", "thousand": ","},
    "VU": {"name_en": "Vanuatu", "name_cn": "瓦努阿图", "currency": "VUV", "symbol": "Vt", "decimal": ".", "thousand": ","},
    "NC": {"name_en": "New Caledonia", "name_cn": "新喀里多尼亚", "currency": "XPF", "symbol": "₣", "decimal": ".", "thousand": ","},
    "PF": {"name_en": "French Polynesia", "name_cn": "法属波利尼西亚", "currency": "XPF", "symbol": "₣", "decimal": ".", "thousand": ","},
    "CK": {"name_en": "Cook Islands", "name_cn": "库克群岛", "currency": "NZD", "symbol": "NZ$", "decimal": ".", "thousand": ","},
    "TO": {"name_en": "Tonga", "name_cn": "汤加", "currency": "TOP", "symbol": "T$", "decimal": ".", "thousand": ","},
    "WS": {"name_en": "Samoa", "name_cn": "萨摩亚", "currency": "WST", "symbol": "$", "decimal": ".", "thousand": ","},
    "KI": {"name_en": "Kiribati", "name_cn": "基里巴斯", "currency": "AUD", "symbol": "A$", "decimal": ".", "thousand": ","},
    "TV": {"name_en": "Tuvalu", "name_cn": "图瓦卢", "currency": "AUD", "symbol": "A$", "decimal": ".", "thousand": ","},
    "NU": {"name_en": "Niue", "name_cn": "纽埃", "currency": "NZD", "symbol": "NZ$", "decimal": ".", "thousand": ","},
    "PW": {"name_en": "Palau", "name_cn": "帕劳", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "MH": {"name_en": "Marshall Islands", "name_cn": "马绍尔群岛", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "FM": {"name_en": "Micronesia", "name_cn": "密克罗尼西亚", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "NR": {"name_en": "Nauru", "name_cn": "瑙鲁", "currency": "AUD", "symbol": "A$", "decimal": ".", "thousand": ","},
    
    # 北欧特殊领土（补充）
    "GL": {"name_en": "Greenland", "name_cn": "格陵兰", "currency": "DKK", "symbol": "kr", "decimal": ".", "thousand": ","},
    "FO": {"name_en": "Faroe Islands", "name_cn": "法罗群岛", "currency": "DKK", "symbol": "kr", "decimal": ".", "thousand": ","},
    "AX": {"name_en": "Aland Islands", "name_cn": "奥兰群岛", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "SJ": {"name_en": "Svalbard and Jan Mayen", "name_cn": "斯瓦尔巴群岛和扬马延岛", "currency": "NOK", "symbol": "kr", "decimal": ".", "thousand": ","},
    "BV": {"name_en": "Bouvet Island", "name_cn": "布韦岛", "currency": "NOK", "symbol": "kr", "decimal": ".", "thousand": ","},
    
    # 澳洲特殊领土（补充）
    "HM": {"name_en": "Heard Island and McDonald Islands", "name_cn": "赫德岛和麦克唐纳群岛", "currency": "AUD", "symbol": "A$", "decimal": ".", "thousand": ","},
    "NF": {"name_en": "Norfolk Island", "name_cn": "诺福克岛", "currency": "AUD", "symbol": "A$", "decimal": ".", "thousand": ","},
    "CX": {"name_en": "Christmas Island", "name_cn": "圣诞岛", "currency": "AUD", "symbol": "A$", "decimal": ".", "thousand": ","},
    "CC": {"name_en": "Cocos Islands", "name_cn": "科科斯群岛", "currency": "AUD", "symbol": "A$", "decimal": ".", "thousand": ","},
    "TF": {"name_en": "French Southern Territories", "name_cn": "法属南部领土", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    
    # 美国领土（补充）
    "AS": {"name_en": "American Samoa", "name_cn": "美属萨摩亚", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "GU": {"name_en": "Guam", "name_cn": "关岛", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "MP": {"name_en": "Northern Mariana Islands", "name_cn": "北马里亚纳群岛", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "VI": {"name_en": "U.S. Virgin Islands", "name_cn": "美属维尔京群岛", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "PR": {"name_en": "Puerto Rico", "name_cn": "波多黎各", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "UM": {"name_en": "U.S. Minor Outlying Islands", "name_cn": "美国本土外小岛屿", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    
    # 法国海外领土（补充）
    "MQ": {"name_en": "Martinique", "name_cn": "马提尼克", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "GP": {"name_en": "Guadeloupe", "name_cn": "瓜德罗普", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "BL": {"name_en": "Saint Barthelemy", "name_cn": "圣巴泰勒米", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "MF": {"name_en": "Saint Martin", "name_cn": "法属圣马丁", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "PM": {"name_en": "Saint Pierre and Miquelon", "name_cn": "圣皮埃尔和密克隆", "currency": "EUR", "symbol": "€", "decimal": ".", "thousand": ","},
    "WF": {"name_en": "Wallis and Futuna", "name_cn": "瓦利斯和富图纳", "currency": "XPF", "symbol": "₣", "decimal": ".", "thousand": ","},
    
    # 英国海外领土（补充）
    "MS": {"name_en": "Montserrat", "name_cn": "蒙特塞拉特", "currency": "XCD", "symbol": "$", "decimal": ".", "thousand": ","},
    "TC": {"name_en": "Turks and Caicos Islands", "name_cn": "特克斯和凯科斯群岛", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "VG": {"name_en": "British Virgin Islands", "name_cn": "英属维尔京群岛", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
    "AI": {"name_en": "Anguilla", "name_cn": "安圭拉", "currency": "XCD", "symbol": "$", "decimal": ".", "thousand": ","},
    "BM": {"name_en": "Bermuda", "name_cn": "百慕大", "currency": "BMD", "symbol": "$", "decimal": ".", "thousand": ","},
    "KY": {"name_en": "Cayman Islands", "name_cn": "开曼群岛", "currency": "KYD", "symbol": "$", "decimal": ".", "thousand": ","},
    "FK": {"name_en": "Falkland Islands", "name_cn": "福克兰群岛", "currency": "FKP", "symbol": "£", "decimal": ".", "thousand": ","},
    "GS": {"name_en": "South Georgia and the South Sandwich Islands", "name_cn": "南乔治亚岛和南桑威奇群岛", "currency": "GBP", "symbol": "£", "decimal": ".", "thousand": ","},
    "SH": {"name_en": "Saint Helena", "name_cn": "圣赫勒拿", "currency": "SHP", "symbol": "£", "decimal": ".", "thousand": ","},
    "IO": {"name_en": "British Indian Ocean Territory", "name_cn": "英属印度洋领土", "currency": "USD", "symbol": "$", "decimal": ".", "thousand": ","},
}

# Plan Name Standardization Mappings
PLAN_NAME_MAP = {
    # English variants
    "netflix mobile": "Mobile",
    "netflix basic": "Basic", 
    "netflix standard": "Standard",
    "netflix premium": "Premium",
    "standard with ads": "Standard with ads",
    "mobile plan": "Mobile",
    "basic plan": "Basic",
    "standard plan": "Standard", 
    "premium plan": "Premium",
    # Generic
    "mobile": "Mobile",
    "basic": "Basic",
    "standard": "Standard",
    "premium": "Premium"
}

# Currency Symbols/Codes to Standard API Codes
CURRENCY_SYMBOLS_TO_CODES = {
    '€': 'EUR', '£': 'GBP', 'usd': 'USD', 'cad': 'CAD', 'ars': 'ARS', 'aud': 'AUD',
    'brl': 'BRL', 'clp': 'CLP', 'cop': 'COP', 'czk': 'CZK', 'dkk': 'DKK', 'hkd': 'HKD',
    'huf': 'HUF', 'jpy': 'JPY', 'mxn': 'MXN', 'nok': 'NOK', 'nzd': 'NZD', 'pen': 'PEN',
    'pln': 'PLN', 'ron': 'RON', 'sek': 'SEK', 'sgd': 'SGD', 'chf': 'CHF', 'twd': 'TWD',
    'try': 'TRY', 'krw': 'KRW', 'inr': 'INR', 'thb': 'THB', 'myr': 'MYR', 'php': 'PHP',
    'idr': 'IDR', 'ngn': 'NGN', 'zar': 'ZAR', 'kes': 'KES', 'egp': 'EGP', 'mad': 'MAD',
    'tnd': 'TND', 'ghs': 'GHS', 'ugx': 'UGX', 'tzs': 'TZS', 'mzn': 'MZN', 'zmw': 'ZMW',
    'bgn': 'BGN', 'isk': 'ISK', 'ils': 'ILS', 'aed': 'AED', 'sar': 'SAR', 'pkr': 'PKR',
    'bdt': 'BDT', 'lkr': 'LKR', 'npr': 'NPR', 'mmk': 'MMK', 'khr': 'KHR', 'lak': 'LAK',
    'vnd': 'VND', 'fjd': 'FJD', 'pgk': 'PGK',
    'lei': 'RON', 'kr': 'DKK', 'tl': 'TRY', 'zł': 'PLN', 'r$': 'BRL', 'ca$': 'CAD',
    'a$': 'AUD', 'hk$': 'HKD', 's$': 'SGD', 'mx$': 'MXN', 'nz$': 'NZD', '₹': 'INR',
    'ntd': 'TWD', 'rm': 'MYR',
    # 新增货币符号映射
    'rsd': 'RSD', 'din': 'RSD', 'bam': 'BAM', 'км': 'BAM', 'mkd': 'MKD', 'ден': 'MKD',
    'all': 'ALL', 'uah': 'UAH', '₴': 'UAH', 'byn': 'BYN', 'br': 'BYN', 'mdl': 'MDL',
    'gel': 'GEL', '₾': 'GEL', 'amd': 'AMD', '֏': 'AMD', 'azn': 'AZN', '₼': 'AZN',
    'kzt': 'KZT', '₸': 'KZT', 'kgs': 'KGS', 'с': 'KGS', 'tjs': 'TJS', 'ѕм': 'TJS',
    'tmt': 'TMT', 'uzs': 'UZS', 'soʻm': 'UZS',
    # 中东地区货币符号
    'qar': 'QAR', '﷼': 'QAR', 'kwd': 'KWD', 'د.ك': 'KWD', 'bhd': 'BHD', 'د.ب': 'BHD',
    'omr': 'OMR', 'jod': 'JOD', 'د.ا': 'JOD', 'lbp': 'LBP', 'ل.ل': 'LBP', 'iqd': 'IQD',
    'د.ع': 'IQD', 'yer': 'YER', 'lyd': 'LYD', 'د.ل': 'LYD',
    # 非洲货币符号
    'dzd': 'DZD', 'د.ج': 'DZD', 'sdg': 'SDG', 'ج.س': 'SDG', 'xof': 'XOF', 'cfa': 'XOF',
    'gnf': 'GNF', 'fg': 'GNF', 'gmd': 'GMD', 'cve': 'CVE', 'mru': 'MRU', 'um': 'MRU',
    'xaf': 'XAF', 'cdf': 'CDF', 'fc': 'CDF', 'stn': 'STN', 'db': 'STN', 'aoa': 'AOA',
    'kz': 'AOA', 'etb': 'ETB', 'rwf': 'RWF', 'frw': 'RWF', 'bif': 'BIF', 'fbu': 'BIF',
    'sos': 'SOS', 'djf': 'DJF', 'fdj': 'DJF', 'ern': 'ERN', 'nfk': 'ERN', 'ssp': 'SSP',
    'mga': 'MGA', 'ar': 'MGA', 'mur': 'MUR', '₨': 'MUR', 'scr': 'SCR', 'kmf': 'KMF',
    'cf': 'KMF',
    # 太平洋货币符号
    'sbd': 'SBD', 'vuv': 'VUV', 'vt': 'VUV', 'xpf': 'XPF', '₣': 'XPF', 'top': 'TOP',
    't$': 'TOP', 'wst': 'WST', 'bmd': 'BMD', 'kyd': 'KYD', 'fkp': 'FKP', 'shp': 'SHP',
    'xcd': 'XCD',
    '¥': 'JPY',
    '$': 'USD'    # Keep generic $ mapping, but logic will prioritize specifics
}

# --- Functions ---

def get_exchange_rates(api_keys, url_template):
    """Fetches exchange rates using a list of API keys."""
    rates = None
    for key in api_keys:
        url = url_template.format(key)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'rates' in data:
                print(f"成功使用 API 密钥 ...{key[-4:]} 获取汇率")
                rates = data['rates']
                if 'USD' not in rates: rates['USD'] = 1.0
                return rates
            else:
                print(f"API 密钥 ...{key[-4:]} 可能无效或受限: {data.get('description')}")
        except requests.exceptions.RequestException as e:
            print(f"使用密钥 ...{key[-4:]} 获取汇率时出错: {e}")
        except json.JSONDecodeError:
             print(f"使用密钥 ...{key[-4:]} 解码 JSON 响应时出错")
    print("无法使用所有提供的 API 密钥获取汇率。")
    return None

def standardize_plan_name(original_name):
    """Standardizes plan names to English using the PLAN_NAME_MAP."""
    name_lower = original_name.lower().strip()
    if name_lower in PLAN_NAME_MAP:
        return PLAN_NAME_MAP[name_lower]
    return ' '.join(original_name.strip().split()).title()

def clean_and_convert_price(raw_amount_str, country_formatting):
    """Cleans price string based on country formatting and converts to Decimal."""
    if not raw_amount_str: return None
    decimal_separator = country_formatting.get('decimal', '.')
    thousand_separator = country_formatting.get('thousand', ',')
    amount_str = re.sub(r'(?:[€£$¥₹]|(?:[A-Z]{2,3}\$?))\s*', '', raw_amount_str, flags=re.IGNORECASE).strip()
    amount_str = re.sub(r'\s*(?:[€£$¥₹]|(?:[A-Z]{2,3}\$?))', '', amount_str, flags=re.IGNORECASE).strip()
    
    # 智能检测：如果字符串只包含数字和一个分隔符，且分隔符后少于3位数字，则认为是小数点
    # 否则认为是千位分隔符（如 15,999 应该是整数，不是 15.999）
    if ',' in amount_str and '.' not in amount_str:
        # 只有逗号，检查逗号后的位数
        comma_parts = amount_str.split(',')
        if len(comma_parts) == 2 and len(comma_parts[1]) == 3:
            # 如果逗号后正好3位数字，很可能是千位分隔符
            amount_str = amount_str.replace(',', '')
        elif len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
            # 如果逗号后1-2位数字，很可能是小数点
            amount_str = amount_str.replace(',', '.')
        else:
            # 多个逗号或其他情况，移除所有逗号作为千位分隔符
            amount_str = amount_str.replace(',', '')
    elif '.' in amount_str and ',' not in amount_str:
        # 只有点，检查点后的位数
        dot_parts = amount_str.split('.')
        if len(dot_parts) == 2 and len(dot_parts[1]) == 3:
            # 如果点后正好3位数字，很可能是千位分隔符
            amount_str = amount_str.replace('.', '')
        # 否则保持原样，认为是小数点
    elif ',' in amount_str and '.' in amount_str:
        # 同时有逗号和点，按照国际标准：最后一个分隔符是小数点，前面的是千位分隔符
        if amount_str.rfind(',') > amount_str.rfind('.'):
            # 逗号在后面，逗号是小数点，点是千位分隔符
            amount_str = amount_str.replace('.', '').replace(',', '.')
        else:
            # 点在后面，点是小数点，逗号是千位分隔符
            amount_str = amount_str.replace(',', '')
    
    # 原有的处理逻辑保持不变作为后备
    if amount_str.count('.') > 1:
        parts = amount_str.split('.')
        amount_str = parts[0] + '.' + ''.join(parts[1:])
    try:
        if not amount_str: return None
        return Decimal(amount_str)
    except InvalidOperation:
         original_cleaned = re.sub(r'\s', '', raw_amount_str)
         only_digits_and_thousand = all(c.isdigit() or c == thousand_separator for c in original_cleaned if not c.isalpha() and c not in ['€','£','$','¥','₹'])
         if only_digits_and_thousand and thousand_separator:
             try:
                  int_str = original_cleaned.replace(thousand_separator, '')
                  if int_str: return Decimal(int_str)
             except InvalidOperation: pass
         print(f"警告：无法将清理后的字符串 '{amount_str}' (来自 '{raw_amount_str}') 转换为 Decimal。")
         return None
    except Exception as e:
        print(f"警告：转换价格时发生意外错误 '{amount_str}' (来自 '{raw_amount_str}'). 错误: {e}")
        return None

def extract_prices_and_currency(price_text, country_details):
    """Extracts monthly/annual prices and determines currency, using country formatting and refined symbol logic."""
    prices = {}
    default_currency_code = country_details.get('currency')
    default_symbol = country_details.get('symbol')
    country_formatting = {
        'decimal': country_details.get('decimal', '.'),
        'thousand': country_details.get('thousand', ',')
    }

    # --- Refined Currency Detection ---
    detected_code = default_currency_code

    # 1. Check for explicit 3-letter codes first
    code_match = re.search(r'\b([A-Z]{3})\b', price_text)
    if code_match:
        explicit_code = code_match.group(1)
        if explicit_code in CURRENCY_SYMBOLS_TO_CODES.values() or explicit_code == default_currency_code:
             if explicit_code != detected_code:
                  print(f"  注意：检测到明确代码 '{explicit_code}'，与默认 '{detected_code}' 不同。使用 '{explicit_code}'。")
                  detected_code = explicit_code

    # 2. If no overriding code found yet, check for specific symbols
    if detected_code == default_currency_code:
        sorted_symbols = sorted(CURRENCY_SYMBOLS_TO_CODES.keys(), key=len, reverse=True)
        found_symbol_code = None
        specific_symbol_matched = False

        for symbol_key in sorted_symbols:
             pattern = r'\b' + re.escape(symbol_key) + r'\b' if symbol_key.isalpha() else re.escape(symbol_key)
             if re.search(pattern, price_text, re.IGNORECASE):
                 potential_code = CURRENCY_SYMBOLS_TO_CODES[symbol_key.lower()]

                 if default_symbol and symbol_key.lower() == default_symbol.lower():
                      found_symbol_code = potential_code
                      specific_symbol_matched = True
                      try:
                          print(f"  调试：匹配到默认符号 '{symbol_key}' -> '{potential_code}'。")
                      except UnicodeEncodeError:
                          print(f"  调试：匹配到默认符号 -> '{potential_code}'。")
                      break

                 elif symbol_key != '$':
                      if found_symbol_code is None:
                           found_symbol_code = potential_code
                           try:
                               print(f"  调试：匹配到特定符号 '{symbol_key}' -> '{potential_code}'。")
                           except UnicodeEncodeError:
                               print(f"  调试：匹配到特定符号 -> '{potential_code}'。")

                 elif symbol_key == '$':
                      if found_symbol_code is None:
                           if default_currency_code in ['USD', 'CAD', 'AUD', 'NZD', 'MXN', 'SGD', 'HKD']:
                                found_symbol_code = potential_code
                                try:
                                    print(f"  调试：匹配到通用 '$'，默认货币 ({default_currency_code}) 使用 '$'，映射到 '{potential_code}'。")
                                except UnicodeEncodeError:
                                    print(f"  调试：匹配到通用 '$'，映射到 '{potential_code}'。")
                           else:
                                try:
                                    print(f"  调试：匹配到通用 '$'，但默认货币 ({default_currency_code}) 不使用。暂时忽略。")
                                except UnicodeEncodeError:
                                    print("  调试：匹配到通用 '$'，但默认货币不使用。暂时忽略。")
                                pass

        if found_symbol_code and (specific_symbol_matched or found_symbol_code != 'USD' or default_currency_code in ['USD', 'CAD', 'AUD', 'NZD', 'MXN', 'SGD', 'HKD']):
             if found_symbol_code != detected_code:
                  try:
                      print(f"  注意：检测到符号代码 '{found_symbol_code}'，与默认 '{detected_code}' 不同。使用 '{found_symbol_code}'。")
                  except UnicodeEncodeError:
                      print(f"  注意：检测到符号代码，使用 '{found_symbol_code}'。")
                  detected_code = found_symbol_code

    final_currency_code = detected_code
    if not final_currency_code:
        print(f"警告：国家/地区 {country_details.get('name_en')} 最终无法确定货币代码。")
        return {}, None

    # --- Price Extraction ---
    patterns = {
        'monthly': r'(?:monthly|mensual|mensuel|maandelijks|monatlich|month|/month)\s*:?\s*([€£$¥₹]?\s?[\d.,]+(?:\s?[A-Z]{3}\$?)?)',
        'annual':  r'(?:annual|anual|annuel|jaarlijks|jährlich|year|/year)\s*:?\s*([€£$¥₹]?\s?[\d.,]+(?:\s?[A-Z]{3}\$?)?)'
    }
    cleaned_text = price_text.replace('\n', ' ').strip()
    for period, pattern in patterns.items():
        matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
        if matches:
            raw_amount = matches[-1].strip()
            decimal_price = clean_and_convert_price(raw_amount, country_formatting)
            if decimal_price is not None: prices[period] = decimal_price

    # Fallback for formats like "HK$81/month or HK$810/year"
    if not prices or len(prices) < 2:
         simple_matches = re.findall(r'([A-Z]{2,3}\$?|[€£$¥₹])\s?([\d.,]+)\s?/(month|year)', cleaned_text, re.IGNORECASE)
         if len(simple_matches) >= 1 :
             for curr_sym, amount_str, period_str in simple_matches:
                 period_key = 'monthly' if 'month' in period_str.lower() else 'annual'
                 if period_key not in prices:
                     decimal_price = clean_and_convert_price(amount_str, country_formatting)
                     if decimal_price is not None: prices[period_key] = decimal_price

    # Fallback for single price entries
    if not prices:
        single_price_match = re.search(r'(?:[A-Z]{2,3}\$?|[€£$¥₹])\s*([\d.,]+)|([\d.,]+)\s*(?:[A-Z]{2,3}\$?|[€£$¥₹])', cleaned_text, re.IGNORECASE)
        raw_amount = None
        if single_price_match: raw_amount = single_price_match.group(1) or single_price_match.group(2)
        else:
             numeric_match = re.search(r'([\d.,]+)', cleaned_text)
             if numeric_match: raw_amount = numeric_match.group(1)
        if raw_amount:
            decimal_price = clean_and_convert_price(raw_amount, country_formatting)
            if decimal_price is not None: prices['monthly'] = decimal_price

    return prices, final_currency_code

def convert_to_cny(amount, currency_code, rates):
    """Converts an amount from a given currency to CNY via USD."""
    if not isinstance(amount, Decimal): return None
    if not rates or not currency_code or currency_code not in rates or 'CNY' not in rates: return None
    try:
        cny_rate = Decimal(rates['CNY'])
        if currency_code == 'USD': cny_amount = amount * cny_rate
        else:
            original_rate = Decimal(rates[currency_code])
            if original_rate == 0:
                 print(f"警告：{currency_code} 的汇率为零。")
                 return None
            usd_amount = amount / original_rate
            cny_amount = usd_amount * cny_rate
        return cny_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception as e:
        print(f"转换 {amount} {currency_code} 时出错: {e}")
        return None

def sort_by_premium_plan_cny(processed_data):
    """按"Premium"套餐的CNY月度价格从低到高排序国家，并在JSON前面添加最便宜的10个。"""
    countries_with_plan_price = []
    countries_without_plan_price = []
    
    for country_code, country_info in processed_data.items():
        target_plan = None
        
        # 精确查找名为"Premium"的套餐
        for plan in country_info.get('plans', []):
            if plan.get('plan_name') == "Premium":
                target_plan = plan
                break
        
        if target_plan and target_plan.get('monthly_price_cny') is not None:
            price_cny_str = target_plan['monthly_price_cny'].replace('CNY ', '')
            try:
                price_cny = float(price_cny_str)
                countries_with_plan_price.append((country_code, price_cny, country_info, target_plan))
            except (ValueError, TypeError):
                countries_without_plan_price.append((country_code, country_info))
        else:
            countries_without_plan_price.append((country_code, country_info))
            
    # 按CNY价格排序
    countries_with_plan_price.sort(key=lambda x: x[1])
    
    # 创建排序后的结果
    sorted_data = {}
    
    # 添加Top 10摘要
    top_10_cheapest = []
    for i, (country_code, price_cny, country_info, plan) in enumerate(countries_with_plan_price[:10]):
        country_name_cn = COUNTRY_INFO.get(country_code, {}).get('name_cn', country_info.get('name_cn', country_code))
        
        top_10_cheapest.append({
            'rank': i + 1,
            'country_code': country_code,
            'country_name_cn': country_name_cn,
            'plan_name': plan.get('plan_name'),
            'original_price': plan.get('monthly_price_original'),
            'currency': plan.get('currency_code'),
            'price_cny': price_cny
        })
        
    sorted_data['_top_10_cheapest_premium_plans'] = {
        'description': '最便宜的10个Netflix Premium套餐 (按月付)',
        'updated_at': time.strftime('%Y-%m-%d'),
        'data': top_10_cheapest
    }
    
    # 添加所有国家的数据
    for country_code, price_cny, country_info, plan in countries_with_plan_price:
        sorted_data[country_code] = country_info
        
    for country_code, country_info in countries_without_plan_price:
        sorted_data[country_code] = country_info
        
    return sorted_data

# --- Main Script ---

# 1. Fetch Exchange Rates
print("正在获取汇率...")
exchange_rates = get_exchange_rates(API_KEYS, API_URL_TEMPLATE)
if not exchange_rates: exit()
else:
    print(f"基础货币: USD。找到 {len(exchange_rates)} 个汇率。")
    if 'CNY' in exchange_rates: print(f"USD 到 CNY 汇率: {exchange_rates['CNY']:.4f}")
    else: print("警告：获取的数据中未找到 CNY 汇率！")

# 2. Load Input JSON
print(f"正在从 {INPUT_JSON_PATH} 加载数据...")
try:
    with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f: data = json.load(f)
    print("数据加载成功。")
except FileNotFoundError: print(f"错误：输入文件未找到于 {INPUT_JSON_PATH}"); exit()
except json.JSONDecodeError as e: print(f"错误：无法解码来自 {INPUT_JSON_PATH} 的 JSON: {e}"); exit()
except Exception as e: print(f"加载文件时发生意外错误: {e}"); exit()

# 3. Process Data
print("正在处理订阅数据...")
processed_data = {}

for country_iso, plans in data.items():
    country_iso_upper = country_iso.upper()
    if country_iso_upper not in COUNTRY_INFO:
        print(f"警告：跳过国家/地区 {country_iso} - 在 COUNTRY_INFO 中未找到信息。")
        continue

    country_details = COUNTRY_INFO[country_iso_upper]
    country_name_cn = country_details.get('name_cn', country_details.get('name_en', country_iso))
    processed_plans_list = []
    print(f"正在处理 {country_name_cn} ({country_iso_upper})...")

    for plan_info in plans:
        original_plan_name = plan_info.get('plan', 'Unknown Plan')
        price_text = plan_info.get('price', '')
        if not price_text:
            print(f"  跳过计划 '{original_plan_name}' - 无价格文本。")
            continue

        standard_plan_name = standardize_plan_name(original_plan_name)
        extracted_prices, final_currency_code = extract_prices_and_currency(price_text, country_details)

        plan_output = {
            "plan_name": standard_plan_name,
            "currency_code": final_currency_code if final_currency_code else "N/A",
            "monthly_price_original": None, "monthly_price_cny": None,
            "annual_price_original": None, "annual_price_cny": None,
        }

        if not final_currency_code: print(f"  警告：计划 '{standard_plan_name}' 无法检测到货币，无法进行转换。")
        else:
            if 'monthly' in extracted_prices and extracted_prices['monthly'] is not None:
                monthly_price = extracted_prices['monthly']
                plan_output["monthly_price_original"] = f"{final_currency_code} {monthly_price}"
                cny_equiv = convert_to_cny(monthly_price, final_currency_code, exchange_rates)
                if cny_equiv is not None: plan_output["monthly_price_cny"] = f"CNY {cny_equiv}"

            if 'annual' in extracted_prices and extracted_prices['annual'] is not None:
                annual_price = extracted_prices['annual']
                plan_output["annual_price_original"] = f"{final_currency_code} {annual_price}"
                cny_equiv = convert_to_cny(annual_price, final_currency_code, exchange_rates)
                if cny_equiv is not None: plan_output["annual_price_cny"] = f"CNY {cny_equiv}"

        processed_plans_list.append(plan_output)

    if processed_plans_list:
        processed_data[country_iso_upper] = {"name_cn": country_name_cn, "plans": processed_plans_list}
    else: print(f"  未找到 {country_name_cn} ({country_iso_upper}) 的可处理计划。")

# 4. Sort data and add Top 10
sorted_data = sort_by_premium_plan_cny(processed_data)

# 5. Output Processed Data
print(f"正在将处理后的数据保存到 {OUTPUT_JSON_PATH}...")
try:
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    print("处理完成。输出已保存。")
except Exception as e: print(f"保存输出文件时出错: {e}")