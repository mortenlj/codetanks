#!/usr/bin/env bash

source ~/.virtualenvs/codetanks/bin/activate
codetanks > /tmp/server.log 2>&1 &
sleep 10
gr runRandomizer > /tmp/randomizer1.log 2>&1 &
gr runRandomizer > /tmp/randomizer2.log 2>&1 &
gr runRandomizer > /tmp/randomizer3.log 2>&1 &
sleep 1
codetanks-viewer tcp://fimojoha-w530:13337 &
codetanks_bot tcp://fimojoha-w530:13337
pkill -f Randomizer
pkill -f codetanks
