#!/bin/bash
# IPO监控守护进程管理脚本

# ========== 配置区 ==========
SCRIPT_DIR="/workspace/ipo-monitor"
MAIN_SCRIPT="$SCRIPT_DIR/ipo_monitor.py"
DAEMON_SCRIPT="$SCRIPT_DIR/ipo_daemon.py"
LOG_FILE="$SCRIPT_DIR/daemon.log"
PID_FILE="$SCRIPT_DIR/ipo_daemon.pid"

# WX Pusher 配置（如需改配置，在这里改，或在环境变量中设置）
export WXPUSHER_APP_TOKEN="${WXPUSHER_APP_TOKEN:-}"
export WXPUSHER_UIDS="${WXPUSHER_UIDS:-}"
export WXPUSHER_TOPIC_IDS="${WXPUSHER_TOPIC_IDS:-}"

# ========== 启动 ==========
start_daemon() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "❌ 守护进程已在运行 (PID: $(cat $PID_FILE))"
        exit 1
    fi
    echo "🚀 启动IPO监控守护进程..."
    echo "   APP_TOKEN: ${WXPUSHER_APP_TOKEN:0:8}..."
    echo "   UIDs: $WXPUSHER_UIDS"
    
    # 进入目录，确保相对路径正常工作
    cd "$SCRIPT_DIR" || exit 1
    
    # 启动守护进程（环境变量已通过export传递）
    nohup python3 "$DAEMON_SCRIPT" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ 启动成功 (PID: $(cat $PID_FILE))"
    else
        echo "❌ 启动失败，请查看日志 $LOG_FILE"
        cat "$LOG_FILE" | tail -20
    fi
}

# ========== 停止 ==========
stop_daemon() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo "🛑 停止守护进程 (PID: $PID)..."
        kill "$PID"
        sleep 2
        if kill -0 "$PID" 2>/dev/null; then
            kill -9 "$PID"
            echo "强制终止"
        fi
        rm -f "$PID_FILE"
        echo "✅ 已停止"
    else
        echo "❌ 守护进程未运行"
        rm -f "$PID_FILE" 2>/dev/null
    fi
}

# ========== 状态 ==========
show_status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ 守护进程运行中 (PID: $(cat $PID_FILE))"
        echo ""
        echo "=== 最近日志 ==="
        tail -20 "$LOG_FILE"
    else
        echo "❌ 守护进程未运行"
        echo ""
        echo "启动命令:"
        echo "  export WXPUSHER_APP_TOKEN='你的Token'"
        echo "  export WXPUSHER_UIDS='你的UID'"
        echo "  $0 start"
    fi
}

# ========== 执行一次测试 ==========
run_once() {
    echo "🧪 执行一次测试任务..."
    cd "$SCRIPT_DIR" || exit 1
    python3 "$MAIN_SCRIPT"
}

# ========== 查看日志 ==========
show_log() {
    tail -f "$LOG_FILE"
}

# ========== 主逻辑 ==========
case "$1" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        stop_daemon
        sleep 1
        start_daemon
        ;;
    status)
        show_status
        ;;
    test)
        run_once
        ;;
    log)
        show_log
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|test|log}"
        echo ""
        echo "  start   - 启动守护进程（每天09:00自动推送）"
        echo "  stop    - 停止守护进程"
        echo "  restart - 重启守护进程"
        echo "  status  - 查看状态和日志"
        echo "  test    - 立即执行一次推送测试"
        echo "  log     - 实时查看日志"
        echo ""
        echo "启动前请先设置环境变量:"
        echo "  export WXPUSHER_APP_TOKEN='AT_xxxxxx'"
        echo "  export WXPUSHER_UIDS='UID_xxxxxx'"
        exit 1
        ;;
esac
