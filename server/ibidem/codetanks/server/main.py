#!/usr/bin/env python
# -*- coding: utf-8

import zmq
from ibidem.codetanks.server.game_server import GameServer


def main():
    zmq_context = zmq.Context.instance()
    registration_socket = zmq_context.socket(zmq.REP)
    port = registration_socket.bind_to_random_port("tcp://*")
    print "Ready to accept registrations on tcp://*:%d" % port
    update_socket = zmq_context.socket(zmq.PUSH)
    port = update_socket.bind_to_random_port("tcp://*")
    update_url = "tcp://localhost:%d" % port
    print "Publishing updates on %s" % update_url
    poller = zmq.Poller()
    poller.register(registration_socket)
    game_server = GameServer()

    viewers = 0

    while True:
        socks = dict(poller.poll(1))
        if registration_socket in socks and socks[registration_socket] == zmq.POLLIN:
            registration = registration_socket.recv_json()
            print "Received registration: %r" % registration
            registration_socket.send_json({"update_url": update_url})
            viewers += 1
        if viewers:
            game_server.update()
            game_data = game_server.build_game_data()
            #print "Publishing: %r" % game_data
            update_socket.send_json(game_data)


if __name__ == "__main__":
    pass
