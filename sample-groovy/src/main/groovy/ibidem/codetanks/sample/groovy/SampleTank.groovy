package ibidem.codetanks.sample.groovy

import groovy.util.logging.Log4j2
import ibidem.codetanks.domain.Aim
import ibidem.codetanks.domain.ClientType
import ibidem.codetanks.domain.CommandReply
import ibidem.codetanks.domain.Death
import ibidem.codetanks.domain.Fire
import ibidem.codetanks.domain.GameInfo
import ibidem.codetanks.domain.Id
import ibidem.codetanks.domain.Move
import ibidem.codetanks.domain.Registration
import ibidem.codetanks.domain.RegistrationReply
import ibidem.codetanks.domain.RegistrationResult
import ibidem.codetanks.domain.Rotate
import ibidem.codetanks.domain.Scan
import ibidem.codetanks.domain.messagesConstants
import org.apache.thrift.TBase
import org.apache.thrift.protocol.TBinaryProtocol
import org.apache.thrift.protocol.TMessage
import org.apache.thrift.protocol.TProtocol
import org.apache.thrift.transport.TIOStreamTransport
import org.apache.thrift.transport.TMemoryInputTransport
import org.zeromq.ZMQ

@Log4j2
class Tank {
    private final CMDS = ["move", "rotate", "aim", "fire", "scan"]
    private final RANDOM = new Random()

    ZMQ.Context ctx
    ZMQ.Socket cmd
    ZMQ.Socket event
    GameInfo gameInfo
    int myId
    boolean isAlive = true

    Tank(def serverUrl) {
        ctx = ZMQ.context(1)
        register(serverUrl)
    }

    static def serialize(TBase value) {
        ByteArrayOutputStream baos = new ByteArrayOutputStream()
        TIOStreamTransport transport = new TIOStreamTransport(baos)
        TProtocol protocol = new TBinaryProtocol.Factory().getProtocol(transport)
        protocol.writeMessageBegin(new TMessage(value.getClass().getSimpleName(), messagesConstants.MESSAGE_WRAPPER_TYPE, 0))
        value.write(protocol)
        protocol.writeMessageEnd()
        baos.toByteArray()
    }

    static def deserialize(byte[] bytes) {
        TMemoryInputTransport transport = new TMemoryInputTransport(bytes);
        TProtocol protocol = new TBinaryProtocol.Factory().getProtocol(transport)
        TMessage message = protocol.readMessageBegin()
        def clazz = Class.forName("ibidem.codetanks.domain."+message.name)
        TBase instance = clazz.newInstance() as TBase
        instance.read(protocol)
        protocol.readMessageEnd()
        instance
    }

    def register(def serverUrl) {
        log.info("Registering at $serverUrl")
        def regSocket = ctx.socket(ZMQ.REQ)
        regSocket.connect(serverUrl)
        def registration = new Registration(ClientType.BOT, new Id('sample-groovy', 1 as short))
        def bytes = serialize(registration)
        regSocket.send(bytes, 0)
        RegistrationReply reply = deserialize(regSocket.recv()) as RegistrationReply
        if (reply.result == RegistrationResult.FAILURE) {
            throw new IllegalStateException("Unable to register for game")
        }
        initSockets(reply)
        gameInfo = reply.game_info
        myId = reply.id
    }

    private initSockets(RegistrationReply reply) {
        log.info("Subscribing to ${reply.event_url}")
        event = ctx.socket(ZMQ.SUB)
        event.subscribe(ZMQ.SUBSCRIPTION_ALL)
        event.connect(reply.event_url)
        log.info("Connecting to ${reply.cmd_url}")
        cmd = ctx.socket(ZMQ.REQ)
        cmd.connect(reply.cmd_url)
    }

    def run() {
        while (isAlive) {
            def delay = (1 + this.RANDOM.nextInt(10)) * 50
            log.info("Sleeping for $delay ms")
            sleep(delay)
            runSingle()
            handleEvents()
        }
    }

    def handleEvents() {
        def bytes = event.recv(ZMQ.NOBLOCK)
        while (bytes != null) {
            def msg = deserialize(bytes)
            if (msg instanceof Death) {
                if (msg.victim.id == myId) {
                    isAlive = false;
                }
            }
            log.info(msg.toString())
            bytes = event.recv(ZMQ.NOBLOCK)
        }
    }

    def runSingle() {
        def nextCmdName = CMDS[this.RANDOM.nextInt(CMDS.size())]
        log.info("Next cmd is $nextCmdName")
        def nextCmd
        switch (nextCmdName) {
            case "move":
                def distance = this.RANDOM.nextInt(gameInfo.arena.height) as short
                nextCmd = new Move(distance)
                break
            case "rotate":
                def angle = this.RANDOM.nextInt(270) as short
                nextCmd = new Rotate(angle)
                break
            case "aim":
                def angle = this.RANDOM.nextInt(270) as short
                nextCmd = new Aim(angle)
                break
            case "fire":
                nextCmd = new Fire()
                break
            case "scan":
                nextCmd = new Scan(10 as short)
                break
            default:
                throw new IllegalStateException("Picked non-existing command: $nextCmdName")
        }
        log.info("Sending cmd: $nextCmd")
        cmd.send(serialize(nextCmd))
        log.info("Waiting for reply")
        CommandReply reply = deserialize(cmd.recv()) as CommandReply
        log.info(reply.toString())
    }
}

if (!args) throw new IllegalStateException("You must supply a server url")
def serverUrl = args.first()
def tank = new Tank(serverUrl)
tank.run()
// Technically, the sockets and context should be closed, and then we could just exit normally,
// but closing the context just hangs the process so we do this instead.
System.exit(0)
