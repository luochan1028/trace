#!/usr/bin/env python3
"""
IPO监控守护进程 - 定时执行监控任务并推送微信
可通过环境变量定制：
- SCHEDULE_TIME: 每日执行时间（默认 "09:00"）
- RUN_ON_START: 启动时是否立即执行一次（默认 "true"）
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime

# 配置
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:00")  # 每天执行时间
RUN_ON_START = os.getenv("RUN_ON_START", "true").lower() == "true"

# 配置日志
LOG_FILE = "/workspace/daemon.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_monitor():
    """执行一次监控任务"""
    logger.info("=" * 60)
    logger.info("开始执行IPO监控任务")
    logger.info("=" * 60)
    try:
        import ipo_monitor
        result = ipo_monitor.main()
        logger.info(f"监控任务执行完成，结果: {len(result)} 个部分")
        return True
    except Exception as e:
        logger.error(f"监控任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def signal_handler(sig, frame):
    """处理终止信号"""
    logger.info("收到终止信号，守护进程退出")
    sys.exit(0)


def main():
    """主循环 - 简单的睡眠检查方式（不依赖额外库）"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 60)
    logger.info(f"IPO监控守护进程启动")
    logger.info(f"  每日执行时间: {SCHEDULE_TIME}")
    logger.info(f"  启动时立即执行: {RUN_ON_START}")
    logger.info("=" * 60)

    # 启动时立即执行一次
    if RUN_ON_START:
        run_monitor()

    last_run_date = None
    while True:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.strftime("%Y-%m-%d")

            # 到点执行
            if current_time == SCHEDULE_TIME and current_date != last_run_date:
                logger.info(f"到达执行时间 {SCHEDULE_TIME}")
                run_monitor()
                last_run_date = current_date

            # 每30秒检查一次
            time.sleep(30)

        except KeyboardInterrupt:
            logger.info("用户中断，守护进程退出")
            break
        except Exception as e:
            logger.error(f"守护进程异常: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
