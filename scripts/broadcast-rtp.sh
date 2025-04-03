#!/bin/sh

ffmpeg -max_delay 0 -max_probe_packets 1 -f v4l2 -framerate 25 -video_size 720x576 -threads 1 -i /dev/video0 -vcodec libx264 -pix_fmt:v yuv420p -g:v 1 -preset ultrafast -tune zerolatency -crf 17 -max_delay 0 -fflags +nobuffer -flags low_delay -f rtp -muxdelay 0 rtp://192.168.20.20:42423
