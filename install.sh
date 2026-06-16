#!/bin/bash
# IPO监控系统一键安装脚本
# 版本: v1.0.0
# 作者: luochan1028
# 用途: 自动下载、安装、配置IPO监控系统

echo "=========================================="
echo "    IPO监控系统一键安装脚本"
echo "=========================================="

# 1. 创建目录
echo ""
echo "[1/5] 创建目录..."
mkdir -p /workspace/ipo-monitor
cd /workspace/ipo-monitor

# 2. 下载代码
echo ""
echo "[2/5] 下载代码..."
if command -v wget >/dev/null 2>&1; then
    wget -q https://github.com/luochan1028/trace/archive/refs/heads/master.tar.gz -O - | tar -xz --strip-components=1
elif command -v curl >/dev/null 2>&1; then
    curl -s https://github.com/luochan1028/trace/archive/refs/heads/master.tar.gz | tar -xz --strip-components=1
else
    echo "错误: 未找到 wget 或 curl"
    exit 1
fi

# 3. 安装依赖
echo ""
echo "[3/5] 安装Python依赖..."
pip install requests beautifulsoup4 -q --break-system-packages

# 4. 设置权限
echo ""
echo "[4/5] 设置权限..."
chmod +x manage.sh run_monitor.sh

# 5. 启动服务
echo ""
echo "[5/5] 启动监控服务..."
export WXPUSHER_APP_TOKEN="AT_QODOEG506OGc9zaKYdGj3g1CoQDx4buE"
export WXPUSHER_UIDS="UID_3BvOCpLVXk46SKf9iHLJ4nmRmh8g"
./manage.sh start

# 6. 显示状态
echo ""
echo "=========================================="
echo "          安装完成!"
echo "=========================================="
./manage.sh status

echo ""
echo "=========================================="
echo "常用命令:"
echo "  ./manage.sh start    # 启动"
echo "  ./manage.sh stop     # 停止"
echo "  ./manage.sh restart  # 重启"
echo "  ./manage.sh status   # 状态"
echo "  ./manage.sh test     # 立即执行一次"
echo "  ./manage.sh log      # 查看日志"
echo "=========================================="