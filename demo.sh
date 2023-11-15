#!/usr/bin/env bash

set -o errexit
set -o pipefail

export TERM=xterm

./earthlyw +all

docker run --label codetanks=server --name codetanks_server --net=host --rm --detach ghcr.io/mortenlj/codetanks-server:latest
docker run --label codetanks=viewer --name codetanks_viewer --net=host -e DISPLAY -v ~/.Xauthority:/root/.Xauthority --rm --detach ghcr.io/mortenlj/codetanks-viewer tcp://localhost:13337
sleep 5

# Launch bots
docker run --label codetanks=sample-groovy-1 --name sample-groovy-1 --net=host --rm --detach ghcr.io/mortenlj/codetanks-sample-groovy tcp://localhost:13337
docker run --label codetanks=sample-groovy-2 --name sample-groovy-2 --net=host --rm --detach ghcr.io/mortenlj/codetanks-sample-groovy tcp://localhost:13337
docker run --label codetanks=sample-groovy-3 --name sample-groovy-3 --net=host --rm --detach ghcr.io/mortenlj/codetanks-sample-groovy tcp://localhost:13337
docker run --label codetanks=rusty-hunter --name rusty-hunter --net=host --rm --detach -e SAMPLE_RUST__SERVER_URI=tcp://localhost:13337 ghcr.io/mortenlj/codetanks-rusty-hunter

docker attach codetanks_server || true

docker container list --filter label=codetanks --quiet | xargs --no-run-if-empty docker container stop
