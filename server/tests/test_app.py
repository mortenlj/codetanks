#!/usr/bin/env python
# -*- coding: utf-8

import re
import zmq
from mock import patch, MagicMock
from nose.tools import eq_, ok_

from ibidem.codetanks.server.main import App, REGISTRATION, UPDATE


def _regex_match(actual, expected):
    ok_(re.match(expected, actual), "%r does not match %r" % (actual, expected))

def _has_key(key, dictionary):
    ok_(dictionary.has_key(key), "%r does not contain key %r" % (dictionary, key))


class TestApp(object):
    def test_app_listens_for_registration_on_given_port(self):
        app = App(54321)
        reg_socket_url = app._socket_urls[REGISTRATION]
        reg_socket = app._sockets[REGISTRATION]
        eq_(reg_socket_url, "tcp://localhost:54321")
        eq_(reg_socket.socket_type, zmq.REP)

    def test_app_publishes_updates_on_random_port(self):
        app = App(None)
        update_socket_url = app._socket_urls[UPDATE]
        update_socket = app._sockets[UPDATE]
        _regex_match(update_socket_url, "tcp://localhost:[0-9]+")
        eq_(update_socket.socket_type, zmq.PUB)

    def test_registering_clients_get_update_url_and_game_info_back(self):
        with patch("zmq.Context.instance", spec=True, new=MagicMock) as context, patch("zmq.Poller", autospec=True) as Poller:
            app = App(None)
            reg_socket = app._sockets[REGISTRATION]
            poller = Poller.return_value
            poller.poll.return_value = {reg_socket: zmq.POLLIN}
            app.run(True)
            reg_socket.send_json.assert_called_once_with({
                "update_url": app._socket_urls[UPDATE],
                "game_info": app.game_server.build_game_info()
            })

    def test_start_event_starts_game_server(self):
        pass

    def test_started_app_sends_game_data_to_update_socket(self):
        pass


if __name__ == "__main__":
    import nose
    nose.main()
