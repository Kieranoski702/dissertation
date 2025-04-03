#!/bin/sh

ffplay -vcodec h264 -max_delay 0 -analyzeduration 1 -protocol_whitelist file,udp,rtp -fflags nobuffer -strict experimental -framedrop -flags low_delay -probesize 32 -vf setpts=0 -sync ext rtp-h264.sdp
