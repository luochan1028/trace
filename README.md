# IPO监控系统

国产芯片IPO上市进度实时监控与微信推送系统。

## 功能特性

- **实时监控**：监控长鑫存储、长江存储、宇树科技、超聚变、昆仑芯、平头哥、紫光展锐、燧原科技等13家未上市独角兽
- **影子股追踪**：同步监控兆易创新、江波龙、北方华创、中微公司、寒武纪、海光信息等6家关联上市股
- **微信推送**：通过WX Pusher自动推送每日监控报告到微信
- **定时任务**：每天09:00自动执行，无需人工干预
- **倒计时提醒**：显示各公司预计上市时间

## 监控对象

### 未上市独角兽

| 公司 | 预计上市 | 核心看点 |
|------|---------|---------|
| 宇树科技 | 2026年7月 | 人形机器人第一股，73天闪电过会 |
| 长鑫存储 | 2026年7-8月 | 全球DRAM第四，Q1净利330亿 |
| 燧原科技 | 2026年7月 | 国产GPU四小龙，腾讯84%持股 |
| 紫光展锐 | 2026年Q3 | 全球手机SoC第四(14%) |
| 超聚变 | 2026年Q4 | 华为系x86服务器龙头 |
| 长江存储 | 2026年底 | NAND全球第三 |
| 昆仑芯 | 2026-2027 | 百度系AI芯片 |
| 平头哥 | 待定 | 阿里系，玄铁50亿颗+ |

### 影子股

| 公司 | 代码 | 关联逻辑 |
|------|------|---------|
| 兆易创新 | 603986 | 参股长鑫存储 |
| 江波龙 | 301308 | 存储模组龙头 |
| 北方华创 | 002371 | 半导体设备 |
| 中微公司 | 688012 | 刻蚀设备 |
| 寒武纪 | 688256 | AI芯片 |
| 海光信息 | 688041 | CPU+DCU |

## 快速部署

### 方式一：一键安装（推荐）

```bash
# 在云主机上执行
bash <(curl -s https://raw.githubusercontent.com/luochan1028/trace/master/install.sh)
```

### 方式二：手动安装

```bash
# 1. 下载代码
mkdir -p /workspace/ipo-monitor && cd /workspace/ipo-monitor
wget https://github.com/luochan1028/trace/archive/refs/heads/master.tar.gz -O - | tar -xz --strip-components=1

# 2. 安装依赖
pip install requests beautifulsoup4 --break-system-packages

# 3. 设置执行权限
chmod +x manage.sh run_monitor.sh

# 4. 配置环境变量
export WXPUSHER_APP_TOKEN='你的AppToken'
export WXPUSHER_UIDS='你的UID'

# 5. 启动服务
./manage.sh start
```

## WX Pusher 配置

### 1. 获取AppToken

1. 访问 [WX Pusher官网](https://wxpusher.zjiecode.com/) 并登录
2. 进入「应用管理」→「创建新应用」
3. 复制 **AppToken**（格式：`AT_xxxxxx`）

### 2. 获取UID

1. 在应用详情页生成二维码
2. 用微信扫码关注应用
3. 在「用户管理」中查看你的 **UID**（格式：`UID_xxxxxx`）

### 3. 配置环境变量

```bash
export WXPUSHER_APP_TOKEN='AT_你的AppToken'
export WXPUSHER_UIDS='UID_你的UID'
```

## 服务管理

```bash
cd /workspace/ipo-monitor

# 启动服务
./manage.sh start

# 停止服务
./manage.sh stop

# 重启服务
./manage.sh restart

# 查看状态
./manage.sh status

# 查看日志
./manage.sh log

# 立即执行一次测试
./manage.sh test
```

## 定时配置

默认每天 **09:00** 自动推送。修改执行时间：

```bash
export SCHEDULE_TIME="18:30"
./manage.sh restart
```

或使用systemd（生产环境推荐）：

```bash
sudo cp ipo-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ipo-monitor
sudo systemctl start ipo-monitor
```

## 目录结构

```
/workspace/ipo-monitor/
├── ipo_monitor.py          # 监控主脚本
├── ipo_daemon.py           # 守护进程
├── manage.sh               # 管理脚本
├── run_monitor.sh          # 启动器
├── ipo-monitor.service     # systemd服务文件
└── daemon.log              # 运行日志
```

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `WXPUSHER_APP_TOKEN` | ✅ | - | WX Pusher AppToken |
| `WXPUSHER_UIDS` | ✅ | - | 接收者UID，多个用逗号分隔 |
| `SCHEDULE_TIME` | ❌ | `09:00` | 每日执行时间 |
| `WXPUSHER_ENABLE` | ❌ | `true` | 是否启用微信推送 |
| `RUN_ON_START` | ❌ | `true` | 启动时是否立即执行一次 |

## 常见问题

### Q: 守护进程启动了但没收到消息？

检查环境变量是否正确配置：
```bash
# 查看当前环境变量
echo $WXPUSHER_APP_TOKEN
echo $WXPUSHER_UIDS
```

### Q: WX Pusher推送失败？

1. 确认AppToken正确
2. 确认UID已关注应用
3. 查看日志：`./manage.sh log`

### Q: 如何添加新的监控公司？

编辑 `ipo_monitor.py`，修改 `MONITORED_COMPANIES` 列表。

## 技术栈

- Python 3
- BeautifulSoup4（网页爬取）
- WX Pusher（微信推送）
- Cron/Linux Crontab（定时任务）

## 免责声明

本系统仅供信息参考，不构成投资建议。投资有风险，决策需谨慎。

## License

MIT
