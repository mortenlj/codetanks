#!/usr/bin/env bash

export TERM=xterm

earthly +all

docker run --label codetanks=server --net=host --rm --detach mortenlj/codetanks-server
sleep 10
docker run --label codetanks=viewer --net=host -e DISPLAY -v ~/.Xauthority:/root/.Xauthority --rm --detach mortenlj/codetanks-viewer tcp://localhost:13337
for i in $(seq 1 3); do
  docker run --label codetanks=sample-groovy-$i --net=host --rm --detach mortenlj/codetanks-sample-groovy tcp://localhost:13337
done
docker run --label codetanks=cli --net=host --rm -ti --entrypoint codetanks_bot mortenlj/codetanks-server tcp://localhost:13337

docker container list --filter label=codetanks --quiet | xargs --no-run-if-empty docker container stop
