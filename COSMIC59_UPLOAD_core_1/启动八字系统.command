#!/bin/bash
cd "$(dirname "$0")"
clear
echo "========================================"
echo "  东方能量命盘 · COSMIC 5.2 Mac"
echo "========================================"
if ! command -v python3 >/dev/null 2>&1; then
  echo "未检测到 Python 3。此 Mac 需要 Python 3 才能运行。"
  read -p "按回车关闭..."; exit 1
fi
PORT=8000
if lsof -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  echo "系统已经运行，正在打开浏览器..."
  open "http://127.0.0.1:$PORT"; exit 0
fi
echo "无需安装 FastAPI / Uvicorn / timezonefinder。"
echo "正在启动系统..."
(sleep 1.5; open "http://127.0.0.1:$PORT") &
echo "浏览器将自动打开。使用期间请保留本窗口。"
echo "停止系统：按 Control + C。"
python3 run_server.py
status=$?
if [ $status -ne 0 ]; then
  echo "启动失败（代码 $status）。"
  read -p "按回车关闭..."
fi
