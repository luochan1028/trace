#!/bin/bash
# IPO监控守护进程管理脚本

DAEMON_SCRIPT="/workspace/ipo-monitor/ipo_daemon.py"
DAEMON_LOG="/workspace/ipo-monitor/daemon.log"
PID_FILE="/workspace/ipo-monitor/ipo_daemon.pid"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "❌ 守护进程已在运行 (PID: $(cat $PID_FILE))"
            exit 1
        fi
        echo "🚀 启动IPO监控守护进程..."
        nohup python3 "$DAEMON_SCRIPT" >> "$DAEMON_LOG" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 2
        if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "✅ 启动成功 (PID: $(cat $PID_FILE))"
        else
            echo "❌ 启动失败，请查看日志 $DAEMON_LOG"
        fi
        ;;
    stop)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            PID=$(cat "$PID_FILE")
            echo "🛑 停止守护进程 (PID: $PID)..."
            kill $PID
            sleep 2
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID
                echo "强制终止"
            fi
            rm -f "$PID_FILE"
            echo "✅ 已停止"
        else
            echo "❌ 守护进程未运行"
            rm -f "$PID_FILE"
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "✅ 守护进程运行中 (PID: $(cat $PID_FILE))"
            echo ""
            echo "=== 最近日志 ==="
            tail -20 "$DAEMON_LOG"
        else
            echo "❌ 守护进程未运行"
        fi
        ;;
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
    test)
        echo "🧪 执行一次测试任务..."
        python3 /workspace/ipo-monitor/ipo_monitor.py
        ;;
    log)
        tail -f "$DAEMON_LOG"
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|test|log}"
        exit 1
        ;;
esac
