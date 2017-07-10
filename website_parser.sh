#! /bin/bash
c=1
total=${1:-10}
trap "exit" INT
while [ ${c} -le ${total} ]
do
    echo "Looped $c times"
    python3.5 scraper.py
    c=$(($c + 1))
done