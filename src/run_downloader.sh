#!/bin/bash
export HOME="${HOME:-/Users/leedavid}"
export PYTHONIOENCODING=utf-8
PROJECT_DIR="${PROJECT_DIR:-$HOME/Documents/Project/Adult Dream}"
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
cd "$PROJECT_DIR"
/usr/bin/python3 "$PROJECT_DIR/src/download_tg_channel.py" >> "$PROJECT_DIR/download/download.log" 2>&1
/usr/bin/python3 "$PROJECT_DIR/src/xv_pipeline.py" 5 >> "$PROJECT_DIR/download/xv_pipeline.log" 2>&1
