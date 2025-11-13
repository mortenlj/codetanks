from abc import abstractmethod, ABC
from typing import Optional

from ibidem.codetanks.domain import messages_pb2

"""Abstract class describing the interface between the game servier and its peers

A peer is either a viewer, or a bot.
"""


class Peer(ABC):
    """A description of a Peer for the GameServer and the interface it implements"""
    # The registration ID of the peer
    id: messages_pb2.Id
    # The client type of the peer
    client_type: messages_pb2.ClientType

    @abstractmethod
    def handle_event(self, event: messages_pb2.Event) -> None:
        """Send the event on to the peer via appropriate transport"""

    @abstractmethod
    def next_command(self) -> Optional[messages_pb2.Command]:
        """Returns a command if one is ready"""

    @abstractmethod
    def command_reply(self, reply: messages_pb2.CommandReply):
        """The servers reply to the last returned command"""
