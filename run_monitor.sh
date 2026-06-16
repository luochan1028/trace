#!/bin/bash
# IPO监控脚本启动器
# 自动加载环境变量并执行监控

# 切换到脚本所在目录
cd "$(dirname "$0")"

# WX Pusher 配置
export WXPUSHER_APP_TOKEN="AT_QODOEG506OGc9zaKYdGj3g1CoQDx4buE"
export WXPUSHER_UIDS="UID_3BvOCpLVXk46SKf9iHLJ4nmRmh8g"

# 可选：邮件配置（如需同时发邮件，请取消注释并填写）
# export SMTP_SERVER="smtp.gmail.com"
# export SMTP_PORT="587"
# export SENDER_EMAIL="your_email@gmail.com"
# export SENDER_PASSWORD="your_app_password"
# export RECIPIENT_EMAIL="recipient@example.com"
# export AUTO_SEND_EMAIL="true"

# 日志输出
LOG_FILE="/workspace/ipo_monitor_$(date +%Y%m%d).log"

echo "==========================================" >> "$LOG_FILE"
echo "执行时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

/root/.pyenv/shims/python3 /workspace/ipo_monitor.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
echo "退出码: $EXIT_CODE" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
