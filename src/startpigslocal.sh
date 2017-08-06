#!/bin/bash
OUT_FILE="output_"
TXT=".txt"
while IFS='' read -r line || [[ -n "$line" ]]; do
    IFS=' ' read -r -a DATA <<< "$line"
    FLNAME=$OUT_FILE${DATA[0]}$TXT
    nohup python3 -u peer.py ${DATA[0]} ${DATA[1]} &> $FLNAME &
done < "$1"
echo "started all pigs locally"
