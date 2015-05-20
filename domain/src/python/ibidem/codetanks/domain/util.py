#!/usr/bin/env python
# -*- coding: utf-8

from thrift.protocol import TBinaryProtocol
from thrift.transport import TTransport

PROTOCOL_FACTORY = TBinaryProtocol.TBinaryProtocolFactory()


def serialize(value):
    value.validate()
    transport = TTransport.TMemoryBuffer()
    protocol = PROTOCOL_FACTORY.getProtocol(transport)
    value.write(protocol)
    data = transport.getvalue()
    return data


def deserialize(data, value):
    transport = TTransport.TMemoryBuffer(data)
    protocol = PROTOCOL_FACTORY.getProtocol(transport)
    value.read(protocol)
    value.validate()
    return value



if __name__ == "__main__":
    pass
