from dataclasses import dataclass
from queue import Queue
from typing import Generator

import grpc
from ibidem.codetanks.domain import messages_pb2_grpc, messages_pb2

from ibidem.codetanks.server.config import settings


class Channel:
    def __init__(self):
        self.request = Queue()
        self.reply = Queue()

    def _create_url(self, host, port=None):
        url = f"http://{host}"
        return "%s:%d" % (url, port) if port else url

    @property
    def url(self):
        return self._create_url(settings.advertise_address, settings.grpc_port)

    def ready(self):
        return self.request.qsize() > 0

    def recv(self):
        return self.request.get()

    def send(self, value):
        self.reply.put(value)


@dataclass
class Channels:
    event: Channel
    cmd: Channel


class CodeTanksServicer(messages_pb2_grpc.CodeTanksServicer):
    def __init__(self, registration_handler):
        self._registration_handler = registration_handler
        self._channels = {}

    def Register(
            self,
            request: messages_pb2.Registration,
            context: grpc.ServicerContext
    ) -> messages_pb2.RegistrationReply:
        peer = context.peer()
        event_channel = Channel()
        cmd_channel = Channel()
        registration_reply = self._registration_handler(request, event_channel, cmd_channel)
        if registration_reply.result == messages_pb2.RegistrationResult.SUCCESS:
            self._channels[peer] = Channels(event_channel, cmd_channel)
        return registration_reply

    def SendCommand(self, request: messages_pb2.Command, context: grpc.ServicerContext) -> messages_pb2.CommandReply:
        peer = context.peer()
        if peer not in self._channels:
            raise grpc.RpcError(grpc.StatusCode.FAILED_PRECONDITION, "Peer not registered")
        channel = self._channels[peer].cmd
        channel.request.put(request)
        return channel.reply.get()


    def GetEvent(
            self,
            _request: messages_pb2.EventRequest,
            context: grpc.ServicerContext
    ) -> Generator[messages_pb2.Event]:
        peer = context.peer()
        if peer not in self._channels:
            raise grpc.RpcError(grpc.StatusCode.FAILED_PRECONDITION, "Peer not registered")
        channel = self._channels[peer].event
        while True:
            yield channel.reply.get()
