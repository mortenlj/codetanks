#!/usr/bin/env bash

export TERM=xterm

bazel build //sample-groovy:Randomizer_deploy.jar
bazel build //... --output_groups=python_zip_file

python bazel-bin/server/codetanks-server.zip > /tmp/server.log 2>&1 &
server_pid=$!
sleep 10
java -jar bazel-bin/sample-groovy/Randomizer_deploy.jar tcp://localhost:13337 > /tmp/randomizer1.log 2>&1 &
bot_1_pid=$!
java -jar bazel-bin/sample-groovy/Randomizer_deploy.jar tcp://localhost:13337 > /tmp/randomizer2.log 2>&1 &
bot_2_pid=$!
java -jar bazel-bin/sample-groovy/Randomizer_deploy.jar tcp://localhost:13337 > /tmp/randomizer3.log 2>&1 &
bot_3_pid=$!
sleep 1
python bazel-bin/viewer/codetanks-viewer.zip tcp://localhost:13337 &
viewer_pid=$!
python bazel-bin/server/codetanks-bot.zip tcp://localhost:13337

for p in ${server_pid} ${viewer_pid} ${bot_1_pid} ${bot_2_pid} ${bot_3_pid}; do
  kill ${p}
  sleep 2
  kill -9 ${p}
done
