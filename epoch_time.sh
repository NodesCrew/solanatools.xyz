#!/bin/bash 

epochTime() {
  d1=$(date -j -u -f "%Y-%m-%dT%TZ" "$1" "+%s")
  d2=$(date -j -u -f "%Y-%m-%dT%TZ" "$2" "+%s")
  seconds=$((d1 - d2))
  eval "echo $(date -j -u -f "%s" "$seconds" +'$((%s/3600/24)) days %H hours %M minutes %S seconds')"
}

findBlockTime() {
  i=0
  output=$(solana block-time $(($1*432000)) 2> /dev/null | grep Date | cut -d" " -f2)
  while [ $? -ne 0 ]; do
    i=$i+1
    output=$(solana block-time $((($1*432000)+$i)) 2> /dev/null | grep Date | cut -d" " -f2)
  done
  echo $output
}

d1=$(findBlockTime $(($1+1)))
d2=$(findBlockTime $1)

epochTime $d1 $d2





