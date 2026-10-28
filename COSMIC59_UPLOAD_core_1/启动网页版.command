#!/bin/bash
cd "$(dirname "$0")"
clear
echo "正在启动 COSMIC 5.6.1 WEB..."
(sleep 2; open "http://127.0.0.1:8000") &
python3 run_server.py
