#!/bin/bash
export HOME=/Users/leedavid
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
cd "/Users/leedavid/Documents/Project/Adult Dream"
/usr/bin/python3 -c "
import sys
sys.argv = ['', '/Users/leedavid/Documents/Project/Adult Dream/src/download_tg_channel.py']
exec(open('/Users/leedavid/Documents/Project/Adult Dream/src/download_tg_channel.py').read())
" >> "/Users/leedavid/Documents/Project/Adult Dream/download/download.log" 2>&1
