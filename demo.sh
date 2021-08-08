#!/usr/bin/env bash

export TERM=xterm

earthly +all

server_c=$(docker run --net=host --rm --detach mortenlj/codetanks-server)
sleep 10
pushd sample-groovy
./gradlew runRandomizer > /tmp/randomizer1.log 2>&1 &
bot_1_pid=$!
./gradlew runRandomizer > /tmp/randomizer2.log 2>&1 &
bot_2_pid=$!
./gradlew runRandomizer > /tmp/randomizer3.log 2>&1 &
bot_3_pid=$!
sleep 1
viewer_c=$(docker run --net=host -e DISPLAY -v ~/.Xauthority:/root/.Xauthority --rm --detach mortenlj/codetanks-viewer tcp://localhost:13337)
docker run --net=host --rm -ti --entrypoint codetanks_bot mortenlj/codetanks-server tcp://localhost:13337

for p in ${bot_1_pid} ${bot_2_pid} ${bot_3_pid}; do
  kill ${p}
  sleep 2
  kill -9 ${p}
done

for c in ${server_c} ${viewer_c}; do
  docker container stop $c
done
