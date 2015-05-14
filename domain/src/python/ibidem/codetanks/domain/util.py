#!/usr/bin/env python
# -*- coding: utf-8

from thrift.protocol import TBinaryProtocol
from thrift.transport import TTransport

from ibidem.codetanks.domain import ttypes
from ibidem.codetanks.domain.constants import MESSAGE_WRAPPER_TYPE


def serialize(value, protocol_factory=TBinaryProtocol.TBinaryProtocolFactory()):
    value.validate()
    transport = TTransport.TMemoryBuffer()
    protocol = protocol_factory.getProtocol(transport)
    protocol.writeMessageBegin(value.__class__.__name__, MESSAGE_WRAPPER_TYPE, 0)
    value.write(protocol)
    protocol.writeMessageEnd()
    data = transport.getvalue()
    return data


def deserialize(data, protocol_factory=TBinaryProtocol.TBinaryProtocolFactory()):
    transport = TTransport.TMemoryBuffer(data)
    protocol = protocol_factory.getProtocol(transport)
    (tname, _, _) = protocol.readMessageBegin()
    value_class = getattr(ttypes, tname)
    if value_class is None:
        raise TypeError("%s is not a valid type" % tname)
    value = value_class()
    value.read(protocol)
    protocol.readMessageEnd()
    value.validate()
    return value



if __name__ == "__main__":
    pass
