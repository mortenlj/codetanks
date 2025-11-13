from queue import Queue, Empty
from typing import Generator, Optional

import grpc
from ibidem.codetanks.domain import messages_pb2_grpc, messages_pb2

from ibidem.codetanks.server import peer


class GrpcPeer(peer.Peer):
    def __init__(self, registration: messages_pb2.Registration):
        self.id = registration.id
        self.client_type = registration.client_type
        self._event_queue = Queue()
        self._command_queue = Queue(1)
        self._command_reply_queue = Queue(1)

    def handle_event(self, event: messages_pb2.Event) -> None:
        self._event_queue.put_nowait(event)

    def get_events(self) -> Generator[messages_pb2.Event]:
        while True:
            yield self._event_queue.get()

    def queue_command(self, cmd: messages_pb2.Command) -> None:
        self._command_queue.put_nowait(cmd)

    def next_command(self) -> Optional[messages_pb2.Command]:
        try:
            return self._command_queue.get(block=False)
        except Empty:
            return None

    def command_reply(self, reply: messages_pb2.CommandReply) -> None:
        self._command_reply_queue.put_nowait(reply)

    def next_reply(self) -> messages_pb2.CommandReply:
        return self._command_reply_queue.get()


class CodeTanksServicer(messages_pb2_grpc.CodeTanksServicer):
    def __init__(self, registration_handler):
        self._registration_handler = registration_handler
        self._channels = {}
        self._peers = {}

    def Register(
            self,
            request: messages_pb2.Registration,
            context: grpc.ServicerContext
    ) -> messages_pb2.RegistrationReply:
        peer_id = context.peer()
        peer = GrpcPeer(request)

        registration_reply: messages_pb2.RegistrationReply = self._registration_handler(peer)
        if registration_reply.result == messages_pb2.RegistrationResult.SUCCESS:
            self._peers[peer_id] = peer
        return registration_reply

    def SendCommand(self, request: messages_pb2.Command, context: grpc.ServicerContext) -> messages_pb2.CommandReply:
        peer_id = context.peer()
        if peer_id not in self._peers:
            raise grpc.RpcError(grpc.StatusCode.FAILED_PRECONDITION, "Peer not registered")
        peer = self._peers[peer_id]
        peer.queue_command(request)
        return peer.next_reply()

    def GetEvent(
            self,
            _request: messages_pb2.EventRequest,
            context: grpc.ServicerContext
    ) -> Generator[messages_pb2.Event]:
        peer_id = context.peer()
        if peer_id not in self._peers:
            raise grpc.RpcError(grpc.StatusCode.FAILED_PRECONDITION, "Peer not registered")
        peer = self._peers[peer_id]
        yield from peer.get_events()
