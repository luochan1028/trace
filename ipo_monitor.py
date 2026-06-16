#!/usr/bin/env python3
"""
IPO监控脚本 - 监控长鑫存储、长江存储、超聚变等公司上市进度
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict
import json
import os

# 搜索功能 - 使用requests和BeautifulSoup
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_WEB = True
except ImportError:
    HAS_WEB = False

# 邮件配置 - 从环境变量读取或使用默认值(需用户配置)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your_email@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your_app_password")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "recipient@example.com")

# WX Pusher 微信推送配置
WXPUSHER_APP_TOKEN = os.getenv("WXPUSHER_APP_TOKEN", "")
WXPUSHER_UIDS = os.getenv("WXPUSHER_UIDS", "").split(",") if os.getenv("WXPUSHER_UIDS") else []
WXPUSHER_TOPIC_IDS = os.getenv("WXPUSHER_TOPIC_IDS", "").split(",") if os.getenv("WXPUSHER_TOPIC_IDS") else []
WXPUSHER_API_URL = "https://wxpusher.zjiecode.com/api/send/message"

# 监控公司列表 - 分为两大类
# A类：IPO冲刺中（直接监控上市进度）
MONITORED_COMPANIES = [
    "长鑫存储",
    "长江存储",
    "超聚变",
    "昆仑芯",      # 百度系AI芯片
    "平头哥",      # 阿里系芯片
    "紫光展锐",    # 国产手机芯片
    "燧原科技",    # 国产GPU四小龙
    "清微智能",    # 可重构芯片
    "中星微",      # XPU多核异构
    "瀚博半导体",  # 高端GPU
    "华虹半导体",
    "中芯国际"
]

# B类：已上市但与未上市巨头强关联的影子股
SHADOW_STOCKS = [
    "兆易创新",    # 参股长鑫存储
    "江波龙",      # 存储模组
    "北方华创",    # 半导体设备
    "中微公司",    # 刻蚀设备
    "寒武纪",      # AI芯片
    "海光信息",    # CPU+DCU
]


def search_news_google(query: str, num_results: int = 5) -> List[Dict]:
    """使用Google搜索获取新闻"""
    if not HAS_WEB:
        return []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f"https://www.google.com/search?q={query}&tbm=nws"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        results = []
        for item in soup.find_all('div', class_='nDgy9d')[:num_results]:
            title_elem = item.find('div', class_='mCBkyc')
            snippet_elem = item.find('div', class_='GI74Re')
            time_elem = item.find('span', class_='OSrXXb')
            link_elem = item.find('a')

            if title_elem:
                results.append({
                    "title": title_elem.text.strip(),
                    "snippet": snippet_elem.text.strip() if snippet_elem else "",
                    "time": time_elem.text.strip() if time_elem else "",
                    "link": link_elem['href'] if link_elem else ""
                })
        return results
    except Exception as e:
        print(f"搜索出错: {e}")
        return []


def search_bing_news(query: str, num_results: int = 5) -> List[Dict]:
    """使用Bing搜索获取新闻"""
    if not HAS_WEB:
        return []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f"https://www.bing.com/news/search?q={query}&qft=+filterui:date-7d"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        results = []
        for item in soup.find_all('div', class_='news-card')[:num_results]:
            title_elem = item.find('a', class_='title')
            snippet_elem = item.find('p', class_='news-snippet')
            time_elem = item.find('span', class_='news-date')
            link = title_elem['href'] if title_elem else ""

            if title_elem:
                results.append({
                    "title": title_elem.text.strip(),
                    "snippet": snippet_elem.text.strip() if snippet_elem else "",
                    "time": time_elem.text.strip() if time_elem else "",
                    "link": link
                })
        return results
    except Exception as e:
        print(f"Bing搜索出错: {e}")
        return []


def get_company_news(company_name: str) -> List[Dict]:
    """获取特定公司的最新新闻"""
    query = f"{company_name} 上市 IPO 科创板 港股"
    news = search_bing_news(query, 5)
    if not news:
        news = search_news_google(query, 5)
    return news


def generate_html_report(news_data: Dict[str, List[Dict]], shadow_news: Dict[str, List[Dict]] = None) -> str:
    """生成HTML邮件报告"""
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); color: white; padding: 20px; border-radius: 8px; }}
            .section-title {{ background: #ff6b35; color: white; padding: 10px 20px; border-radius: 5px; margin: 20px 0 10px; }}
            .section-title.shadow {{ background: #4caf50; }}
            .company-section {{ margin: 20px 0; }}
            .company-title {{ color: #1a73e8; font-size: 18px; font-weight: bold; margin: 15px 0 10px; }}
            .news-item {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #1a73e8; }}
            .news-title {{ font-weight: bold; color: #202124; }}
            .news-snippet {{ color: #5f6368; margin: 8px 0; }}
            .news-meta {{ color: #80868b; font-size: 12px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #80868b; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📈 国产芯片IPO监控日报</h1>
            <p>监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>📊 监控对象：未上市独角兽 {len(MONITORED_COMPANIES)} 家 + 影子股 {len(SHADOW_STOCKS)} 家</p>
        </div>
    """

    # 第一部分：未上市独角兽IPO动态
    html += '<div class="section-title">🚀 第一部分：未上市国产芯片独角兽</div>'

    for company, news_list in news_data.items():
        if news_list:
            html += f"""
            <div class="company-section">
                <div class="company-title">🏢 {company}</div>
            """
            for news in news_list:
                html += f"""
                <div class="news-item">
                    <div class="news-title">{news['title']}</div>
                    <div class="news-snippet">{news['snippet']}</div>
                    <div class="news-meta">
                        ⏰ {news['time']} | <a href="{news['link']}">查看原文</a>
                    </div>
                </div>
                """
            html += "</div>"

    # 第二部分：影子股动态
    if shadow_news:
        html += '<div class="section-title shadow">📈 第二部分：关联影子股动态</div>'

        for company, news_list in shadow_news.items():
            if news_list:
                html += f"""
                <div class="company-section">
                    <div class="company-title">💎 {company}</div>
                """
                for news in news_list:
                    html += f"""
                    <div class="news-item">
                        <div class="news-title">{news['title']}</div>
                        <div class="news-snippet">{news['snippet']}</div>
                        <div class="news-meta">
                            ⏰ {news['time']} | <a href="{news['link']}">查看原文</a>
                        </div>
                    </div>
                    """
                html += "</div>"

    html += f"""
        <div class="footer">
            <p>此邮件由系统自动发送，请勿回复。</p>
            <p>如需修改监控配置，请联系管理员。</p>
        </div>
    </body>
    </html>
    """
    return html


def generate_markdown_report(news_data: Dict[str, List[Dict]], shadow_news: Dict[str, List[Dict]] = None) -> str:
    """生成Markdown格式报告，用于WX Pusher推送"""
    report = f"# 📈 国产芯片IPO监控日报\n\n"
    report += f"**监控时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += f"**监控对象:** 未上市独角兽 {len(MONITORED_COMPANIES)} 家 + 影子股 {len(SHADOW_STOCKS)} 家\n\n"
    report += "---\n\n"

    # 第一部分：未上市独角兽
    report += "## 🚀 第一部分：未上市国产芯片独角兽\n\n"

    has_news = False
    for company, news_list in news_data.items():
        if news_list:
            has_news = True
            report += f"### 🏢 {company}\n\n"
            for idx, news in enumerate(news_list, 1):
                title = news.get('title', '无标题').strip()
                snippet = news.get('snippet', '').strip()
                time_str = news.get('time', '').strip()
                link = news.get('link', '').strip()

                report += f"**{idx}. {title}**\n"
                if snippet:
                    report += f"> {snippet}\n\n"
                if time_str:
                    report += f"⏰ {time_str}\n"
                if link:
                    report += f"[查看原文]({link})\n"
                report += "\n"

    if not has_news:
        report += "当前未搜索到最新独角兽IPO消息。\n\n"

    # 第二部分：影子股
    if shadow_news:
        report += "---\n\n"
        report += "## 📈 第二部分：关联影子股动态\n\n"
        has_shadow_news = False
        for company, news_list in shadow_news.items():
            if news_list:
                has_shadow_news = True
                report += f"### 💎 {company}\n\n"
                for idx, news in enumerate(news_list, 1):
                    title = news.get('title', '无标题').strip()
                    snippet = news.get('snippet', '').strip()
                    time_str = news.get('time', '').strip()
                    link = news.get('link', '').strip()

                    report += f"**{idx}. {title}**\n"
                    if snippet:
                        report += f"> {snippet}\n\n"
                    if time_str:
                        report += f"⏰ {time_str}\n"
                    if link:
                        report += f"[查看原文]({link})\n"
                    report += "\n"

        if not has_shadow_news:
            report += "当前未搜索到影子股最新消息。\n\n"

    report += "---\n\n"
    report += "*此消息由IPO监控系统自动推送*\n"
    return report


def send_wxpusher(content: str, summary: str = None, content_type: int = 3) -> bool:
    """
    通过WX Pusher发送微信消息
    
    Args:
        content: 消息内容
        summary: 消息摘要（显示在微信通知列表）
        content_type: 1=纯文本, 2=HTML, 3=Markdown（默认）
    """
    if not WXPUSHER_APP_TOKEN:
        print("WX Pusher: 未配置APP_TOKEN，跳过推送")
        return False

    if not WXPUSHER_UIDS and not WXPUSHER_TOPIC_IDS:
        print("WX Pusher: 未配置UID或Topic ID，跳过推送")
        return False

    if not HAS_WEB:
        print("WX Pusher: 缺少requests库，无法发送")
        return False

    payload = {
        "appToken": WXPUSHER_APP_TOKEN,
        "content": content,
        "contentType": content_type,
        "summary": summary or f"IPO监控日报 - {datetime.now().strftime('%Y-%m-%d')}",
        "uids": [uid.strip() for uid in WXPUSHER_UIDS if uid.strip()],
        "topicIds": [int(tid.strip()) for tid in WXPUSHER_TOPIC_IDS if tid.strip().isdigit()],
    }

    try:
        response = requests.post(WXPUSHER_API_URL, json=payload, timeout=15)
        result = response.json()

        if result.get("code") == 1000:
            data = result.get("data", [])
            success_count = sum(1 for item in data if item.get("code") == 1000)
            print(f"WX Pusher: 推送成功，共发送 {success_count}/{len(data)} 个用户")
            return True
        else:
            print(f"WX Pusher: 推送失败 - {result.get('msg', '未知错误')}")
            return False
    except Exception as e:
        print(f"WX Pusher: 推送出错 - {e}")
        return False


def send_email(html_content: str, subject: str = None) -> bool:
    """发送邮件"""
    if not subject:
        subject = f"IPO监控日报 - {datetime.now().strftime('%Y-%m-%d')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"邮件发送成功至 {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("国产芯片IPO监控系统启动")
    print("=" * 60)

    # 第一部分：搜索未上市独角兽IPO动态
    print(f"\n[第一部分] 搜索 {len(MONITORED_COMPANIES)} 家未上市独角兽IPO动态...")
    news_data = {}
    for company in MONITORED_COMPANIES:
        print(f"  - 搜索 {company} ...")
        news = get_company_news(company)
        news_data[company] = news
        print(f"    找到 {len(news)} 条新闻")

    # 第二部分：搜索影子股动态
    print(f"\n[第二部分] 搜索 {len(SHADOW_STOCKS)} 家关联影子股动态...")
    shadow_news = {}
    for company in SHADOW_STOCKS:
        print(f"  - 搜索 {company} ...")
        news = get_company_news(company)
        shadow_news[company] = news
        print(f"    找到 {len(news)} 条新闻")

    # 生成报告
    html_report = generate_html_report(news_data, shadow_news)
    md_report = generate_markdown_report(news_data, shadow_news)

    # 保存报告到文件（备份）
    report_file = f"ipo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_report)
    print(f"\n报告已保存到: {report_file}")

    # WX Pusher 微信推送
    if os.getenv("WXPUSHER_ENABLE", "true").lower() == "true":
        print("\n正在通过WX Pusher推送微信消息...")
        send_wxpusher(md_report)
    else:
        print("WX Pusher推送已禁用 (WXPUSHER_ENABLE=false)")

    # 发送邮件
    if os.getenv("AUTO_SEND_EMAIL", "false").lower() == "true":
        send_email(html_report)
    else:
        print("邮件发送已禁用 (AUTO_SEND_EMAIL=false)")

    print("\n" + "=" * 60)
    print("监控任务完成")
    print("=" * 60)

    return news_data, shadow_news


if __name__ == "__main__":
    main()
