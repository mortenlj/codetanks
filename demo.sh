#!/usr/bin/env bash

export TERM=xterm

./earthlyw +all

./earthlyw ./server/+launch &
sleep 10
docker run --label codetanks=viewer --net=host -e DISPLAY -v ~/.Xauthority:/root/.Xauthority --rm --detach ghcr.io/mortenlj/codetanks-viewer tcp://localhost:13337

for i in $(seq 1 3); do
  docker run --label codetanks=sample-groovy-$i --net=host --rm --detach ghcr.io/mortenlj/codetanks-sample-groovy tcp://localhost:13337
done

docker run --label codetanks=sample-rust --net=host --rm --detach ghcr.io/mortenlj/codetanks-sample-rust tcp://localhost:13337

#docker run --label codetanks=cli --net=host --rm -ti --entrypoint codetanks_bot ghcr.io/mortenlj/codetanks-server tcp://localhost:13337

read

docker container list --filter label=codetanks --quiet | xargs --no-run-if-empty docker container stop
