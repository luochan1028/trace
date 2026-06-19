#!/usr/bin/env python3
"""
国产芯片IPO监控系统 - 每日推送微信通知
核心策略：结构化数据为主，新闻搜索为辅
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ============================================================
# 配置：WX Pusher 推送通道
# ============================================================
WXPUSHER_APP_TOKEN = os.getenv("WXPUSHER_APP_TOKEN", "")
WXPUSHER_UIDS = os.getenv("WXPUSHER_UIDS", "").split(",") if os.getenv("WXPUSHER_UIDS") else []
WXPUSHER_TOPIC_IDS = os.getenv("WXPUSHER_TOPIC_IDS", "").split(",") if os.getenv("WXPUSHER_TOPIC_IDS") else []
WXPUSHER_API_URL = "https://wxpusher.zjiecode.com/api/send/message"

# ============================================================
# 监控公司列表 - 结构化核心数据
# ============================================================
COMPANIES = [
    {
        "name": "长鑫科技",
        "status": "注册生效",
        "status_color": "red",
        "progress_detail": "6月12日证监会同意科创板IPO注册，预计7-8月上市",
        "board": "科创板",
        "valuation": "发行市值待披露，拟募资295亿（科创板第二大IPO）",
        "core_logic": "全球DRAM第四（7.67%），国内唯一自主DRAM量产厂。2026Q1营收508亿，净利润247亿（+1688%）",
        "risk": "DRAM强周期风险，三星/海力士扩产即价格回撤；美国设备禁运",
        "last_update": "2026-06-12",
        "milestones": [
            {"date": "2025-12-30", "event": "上交所受理"},
            {"date": "2026-05-27", "event": "上市委全票通过"},
            {"date": "2026-06-12", "event": "证监会注册生效"},
            {"date": "2026-07-15", "event": "预计上市（估算）"},
        ],
    },
    {
        "name": "宇树科技",
        "status": "过会待注册",
        "status_color": "red",
        "progress_detail": "6月1日过会，已提交证监会注册，预计7月上旬上市",
        "board": "科创板",
        "valuation": "发行估值420亿，机构预测上市后600-1000亿",
        "core_logic": "A股人形机器人第一股。全球四足机器人市占第一，人形机器人全球出货Top1。2025营收17亿(+333%)，净利6亿(+658%)",
        "risk": "70%营收依赖高校科研采购，商用场景待突破；Q1扣非净利同比腰斩(-52%)",
        "last_update": "2026-06-02",
        "milestones": [
            {"date": "2026-03-20", "event": "上交所受理"},
            {"date": "2026-06-01", "event": "上市委审议通过（73天闪电过会）"},
            {"date": "2026-06-02", "event": "提交证监会注册"},
            {"date": "2026-07-05", "event": "预计上市（估算）"},
        ],
    },
    {
        "name": "燧原科技",
        "status": "过会待注册",
        "status_color": "red",
        "progress_detail": "6月15日科创板过会，提交注册中",
        "board": "科创板",
        "valuation": "拟募资60亿，参考摩尔线程/沐曦市值，预计上市后千亿级",
        "core_logic": "国产GPU四小龙之一。云端AI芯片DSA架构，自研GCU-CARE加速单元和GCU-LARE高速互联。腾讯深度绑定",
        "risk": "客户高度集中腾讯（84%）；持续亏损（2025净亏11.6亿）",
        "last_update": "2026-06-15",
        "milestones": [
            {"date": "2026-01-22", "event": "科创板受理"},
            {"date": "2026-06-15", "event": "上市委审议通过"},
            {"date": "2026-07-20", "event": "预计上市（估算）"},
        ],
    },
    {
        "name": "超聚变",
        "status": "已问询",
        "status_color": "blue",
        "progress_detail": "5月22日创业板受理，5月29日进入问询阶段",
        "board": "创业板",
        "valuation": "拟募资80亿，发行估值约600-800亿（河南史上最大IPO）",
        "core_logic": "华为系x86服务器巨头。国内x86服务器市占第二（12.7%），液冷服务器连续4年第一。2025营收582亿",
        "risk": "净利率仅1-2%，毛利率承压；经营现金流持续为负；华为授权依赖",
        "last_update": "2026-05-29",
        "milestones": [
            {"date": "2026-05-22", "event": "创业板IPO获受理"},
            {"date": "2026-05-29", "event": "进入问询阶段"},
            {"date": "2026-09-01", "event": "预计过会（估算）"},
        ],
    },
    {
        "name": "长江存储",
        "status": "辅导备案",
        "status_color": "yellow",
        "progress_detail": "5月19日IPO辅导备案，辅导机构中信证券+中信建投，预计年底/明年初申报",
        "board": "待定（预计科创板）",
        "valuation": "胡润1600亿，市场预期3000-8000亿",
        "core_logic": "中国大陆唯一3D NAND完整IDM厂商。全球NAND份额超10%（部分机构估16.4%超美光）。2026Q1营收200亿(+100%)",
        "risk": "盈利弹性弱于长鑫（Q1净利仅2.5亿vs长鑫247亿）；核心专利被美光无效化；赵伟国案历史遗留",
        "last_update": "2026-05-19",
        "milestones": [
            {"date": "2026-05-19", "event": "辅导备案（中信证券+中信建投）"},
            {"date": "2026-11-01", "event": "预计辅导验收（估算）"},
            {"date": "2027-02-01", "event": "预计申报（估算）"},
        ],
    },
    {
        "name": "紫光展锐",
        "status": "辅导验收",
        "status_color": "yellow",
        "progress_detail": "预计Q2完成辅导验收，随后提交科创板申报",
        "board": "科创板",
        "valuation": "700亿（2024年11月增资后估值）",
        "core_logic": "全球手机SoC第四（14%），大陆除华为外唯一具备完整自研基带能力。2024营收145亿，5G芯片销量+82%",
        "risk": "高端市场空白（旗舰T9100 6nm仍非主流）；AI性能弱；依赖传音低端客户",
        "last_update": "2026-04-20",
        "milestones": [
            {"date": "2025-06-27", "event": "科创板辅导备案"},
            {"date": "2026-06-30", "event": "预计辅导验收（估算）"},
            {"date": "2026-09-15", "event": "预计申报（估算）"},
        ],
    },
    {
        "name": "昆仑芯",
        "status": "双轨推进",
        "status_color": "yellow",
        "progress_detail": "1月已递表港交所，5月同步启动科创板辅导备案（A+H）",
        "board": "科创板+港交所",
        "valuation": "投行报告估值约210亿（对标寒武纪7430亿，折价明显）",
        "core_logic": "百度系AI芯片。2025年营收35亿，外部订单首超50%。中标中国移动十亿级订单。国产AI芯片出货第二（仅次于华为昇腾）",
        "risk": "背靠百度生态但独立性不足；软件生态薄弱；估值相比寒武纪大幅折价",
        "last_update": "2026-05-15",
        "milestones": [
            {"date": "2026-01-XX", "event": "港交所递表"},
            {"date": "2026-05-15", "event": "科创板辅导备案"},
            {"date": "2026-11-01", "event": "预计港股上市（估算）"},
        ],
    },
    {
        "name": "平头哥",
        "status": "意向阶段",
        "status_color": "orange",
        "progress_detail": "2026年1月阿里确认IPO意向，但无具体时间表和申报动作",
        "board": "待定",
        "valuation": "摩根大通估算250-620亿美元（约1800-4500亿人民币）",
        "core_logic": "阿里系全栈芯片。玄铁RISC-V IP全球最成熟，芯片出货50亿颗+。含推理+训练+存储+网络全产品线",
        "risk": "无明确IPO时间表；阿里历史撤回云/菜鸟上市计划；关联交易问题；短期难独立",
        "last_update": "2026-01-20",
        "milestones": [
            {"date": "2026-01-20", "event": "确认IPO意向"},
            {"date": "2026-12-31", "event": "预计启动辅导（估算，高不确定性）"},
        ],
    },
]

# ============================================================
# 工具函数：计算倒计时
# ============================================================
def days_until(date_str: str) -> int:
    """计算距离目标日期的天数"""
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (target - today).days
    except:
        return -999


def days_since(date_str: str) -> int:
    """计算距离目标日期已过去多少天"""
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (today - target).days
    except:
        return -999


# ============================================================
# 新闻搜索：用简单关键词方式，失败不影响主流程
# ============================================================
def search_latest_news(company_name: str, max_items: int = 1) -> List[Dict]:
    """
    搜索最新新闻 - 用简单的 requests 方式，失败不影响主体推送
    """
    if not HAS_REQUESTS:
        return []
    
    try:
        # 直接搜Bing新闻（简化版，不依赖特定CSS结构）
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        query = f"{company_name} IPO 上市 2026"
        url = f"https://www.bing.com/news/search?q={query}&qft=+filterui:date-7d"
        
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return []
        
        # 简单抓取：搜索结果页的<title>和<meta description>
        # 不依赖复杂的CSS选择器，避免结构变更导致抓取失败
        content = resp.text
        results = []
        
        # 抓取包含公司名的标题片段（简单策略）
        import re
        # 匹配新闻标题和摘要
        title_pattern = re.compile(r'<div[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</div>', re.I)
        snippet_pattern = re.compile(r'<div[^>]*class="[^"]*snippet[^"]*"[^>]*>(.*?)</div>', re.I)
        
        titles = title_pattern.findall(content)
        snippets = snippet_pattern.findall(content)
        
        for i, title in enumerate(titles[:max_items]):
            # 移除HTML标签
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            clean_snippet = ""
            if i < len(snippets):
                clean_snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            
            if clean_title and len(clean_title) > 5:
                results.append({
                    "title": clean_title[:80],
                    "snippet": clean_snippet[:150],
                })
        
        return results
    except Exception as e:
        logging.debug(f"搜索 {company_name} 新闻失败: {e}")
        return []


# ============================================================
# 生成日报内容（Markdown格式）
# ============================================================
def generate_daily_report() -> str:
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    
    report_lines = []
    report_lines.append(f"# 🔥 国产芯片IPO每日监控")
    report_lines.append(f"")
    report_lines.append(f"**推送时间:** {today.strftime('%Y-%m-%d %H:%M')}")
    report_lines.append(f"**监控公司:** {len(COMPANIES)} 家")
    report_lines.append(f"")
    
    # 按优先级排序：注册生效 → 过会 → 已问询 → 辅导 → 意向
    status_order = {"red": 0, "blue": 1, "yellow": 2, "orange": 3}
    sorted_companies = sorted(COMPANIES, key=lambda c: (status_order.get(c["status_color"], 9), c["name"]))
    
    report_lines.append("---")
    report_lines.append(f"## ⏰ 上市倒计时 TOP")
    report_lines.append(f"")
    
    # 倒计时信息（只展示接近上市的公司）
    upcoming = []
    for c in sorted_companies:
        last_milestone = c["milestones"][-1]
        days = days_until(last_milestone["date"])
        if c["status_color"] in ["red", "blue"]:
            upcoming.append((c["name"], last_milestone["event"], days))
    
    for idx, (name, event, days_left) in enumerate(upcoming, 1):
        if days_left >= 0:
            report_lines.append(f"{idx}. **{name}** - {event}（约 {days_left} 天）")
        else:
            report_lines.append(f"{idx}. **{name}** - {event}（已过{-days_left}天，随时上市）")
    
    report_lines.append(f"")
    report_lines.append("---")
    report_lines.append(f"")
    
    # 每家公司详细信息
    for idx, company in enumerate(sorted_companies, 1):
        name = company["name"]
        status = company["status"]
        progress = company["progress_detail"]
        valuation = company["valuation"]
        core = company["core_logic"]
        risk = company["risk"]
        last_update = company["last_update"]
        
        # 状态图标
        if company["status_color"] == "red":
            status_icon = "🔴"
        elif company["status_color"] == "blue":
            status_icon = "🔵"
        elif company["status_color"] == "yellow":
            status_icon = "🟡"
        else:
            status_icon = "🟠"
        
        report_lines.append(f"## {status_icon} {idx}. {name}")
        report_lines.append(f"")
        report_lines.append(f"**状态:** {status} | {company['board']}")
        report_lines.append(f"")
        report_lines.append(f"**进度:** {progress}")
        report_lines.append(f"")
        report_lines.append(f"**估值/募资:** {valuation}")
        report_lines.append(f"")
        report_lines.append(f"**核心逻辑:** {core}")
        report_lines.append(f"")
        report_lines.append(f"**风险提示:** {risk}")
        report_lines.append(f"")
        
        # 里程碑时间线
        report_lines.append(f"**时间线:**")
        for ms in company["milestones"]:
            days = days_until(ms["date"])
            if days >= 0:
                report_lines.append(f"- `{ms['date']}` → {ms['event']}（{days}天后）")
            else:
                report_lines.append(f"- `{ms['date']}` → ✅ {ms['event']}（已完成）")
        report_lines.append(f"")
        
        # 最近更新时间
        days_ago = days_since(last_update)
        if days_ago >= 0:
            report_lines.append(f"_上次更新: {last_update}（{days_ago}天前）_")
        report_lines.append(f"")
        report_lines.append("---")
        report_lines.append(f"")
    
    # 底部信息
    report_lines.append(f"## 📊 数据说明")
    report_lines.append(f"")
    report_lines.append(f"- 核心数据基于证监会/上交所/港交所公开信息")
    report_lines.append(f"- 预估上市时间为内部估算，仅供参考")
    report_lines.append(f"- 估值数据来自投行研报、招股书披露")
    report_lines.append(f"")
    report_lines.append(f"---")
    report_lines.append(f"*本消息由IPO监控系统每日自动推送 | 数据更新日期: {today_str}*")
    
    return "\n".join(report_lines)


# ============================================================
# WX Pusher 推送
# ============================================================
def send_to_wxpusher(content: str) -> bool:
    """通过WX Pusher推送消息到微信"""
    if not WXPUSHER_APP_TOKEN:
        print("[错误] 未配置 WXPUSHER_APP_TOKEN")
        return False
    
    if not WXPUSHER_UIDS and not WXPUSHER_TOPIC_IDS:
        print("[错误] 未配置 WXPUSHER_UIDS 或 WXPUSHER_TOPIC_IDS")
        return False
    
    if not HAS_REQUESTS:
        print("[错误] 缺少 requests 库")
        return False
    
    payload = {
        "appToken": WXPUSHER_APP_TOKEN,
        "content": content,
        "contentType": 3,  # Markdown
        "summary": f"IPO监控日报 | {datetime.now().strftime('%m-%d')} | 关注{len(COMPANIES)}家",
        "uids": [uid.strip() for uid in WXPUSHER_UIDS if uid.strip()],
    }
    
    # 添加topicIds（如果有）
    topic_ids = [tid.strip() for tid in WXPUSHER_TOPIC_IDS if tid.strip()]
    if topic_ids:
        payload["topicIds"] = topic_ids
    
    try:
        resp = requests.post(WXPUSHER_API_URL, json=payload, timeout=15)
        result = resp.json()
        
        if result.get("code") == 1000:
            data = result.get("data", [])
            success = sum(1 for item in data if item.get("code") == 1000)
            print(f"[成功] 推送到 {success}/{len(data)} 个用户")
            return True
        else:
            print(f"[失败] WX Pusher返回: {result}")
            return False
    except Exception as e:
        print(f"[失败] 推送异常: {e}")
        return False


# ============================================================
# 主入口
# ============================================================
def main():
    print("=" * 60)
    print(f"国产芯片IPO监控系统 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 生成报告
    report = generate_daily_report()
    print(f"\n报告内容生成完成（{len(report)}字符）")
    
    # 推送微信
    print("\n正在推送微信消息...")
    if send_to_wxpusher(report):
        print("✅ 推送成功！")
    else:
        print("❌ 推送失败，请检查配置")
        # 打印调试信息
        print(f"  Token配置: {'已配置' if WXPUSHER_APP_TOKEN else '未配置'}")
        print(f"  UIDs: {WXPUSHER_UIDS}")
    
    print("\n" + "=" * 60)
    print("监控任务完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
