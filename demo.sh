#!/usr/bin/env bash

export TERM=xterm

codetanks > /tmp/server.log 2>&1 &
server_pid=$!
sleep 10
pushd sample-groovy
./gradlew runRandomizer > /tmp/randomizer1.log 2>&1 &
bot_1_pid=$!
./gradlew runRandomizer > /tmp/randomizer2.log 2>&1 &
bot_2_pid=$!
./gradlew runRandomizer > /tmp/randomizer3.log 2>&1 &
bot_3_pid=$!
sleep 1
codetanks-viewer tcp://localhost:13337 &
viewer_pid=$!
codetanks_bot tcp://localhost:13337

for p in ${server_pid} ${viewer_pid} ${bot_1_pid} ${bot_2_pid} ${bot_3_pid}; do
  kill ${p}
  sleep 2
  kill -9 ${p}
done
