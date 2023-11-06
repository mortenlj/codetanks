package ibidem.codetanks.sample.groovy

import com.google.protobuf.Descriptors
import com.google.protobuf.Message
import groovy.util.logging.Log4j2
import ibidem.codetanks.domain.Messages
import ibidem.codetanks.domain.Messages.ClientType
import ibidem.codetanks.domain.Messages.Command
import ibidem.codetanks.domain.Messages.CommandReply
import ibidem.codetanks.domain.Messages.CommandResult
import ibidem.codetanks.domain.Messages.CommandType
import ibidem.codetanks.domain.Messages.Event
import ibidem.codetanks.domain.Messages.GameInfo
import ibidem.codetanks.domain.Messages.Id
import ibidem.codetanks.domain.Messages.Registration
import ibidem.codetanks.domain.Messages.RegistrationReply
import ibidem.codetanks.domain.Messages.RegistrationResult
import org.zeromq.ZMQ

@Log4j2
class Tank {
    private final RANDOM = new Random()

    ZMQ.Context ctx
    ZMQ.Socket cmdSocket
    ZMQ.Socket eventSocket
    GameInfo gameInfo
    int myId
    boolean isAlive = true
    boolean ready = true

    Tank(def serverUrl) {
        ctx = ZMQ.context(1)
        register(serverUrl)
    }

    static def serialize(Message value) {
        value.toByteArray()
    }

    static <T extends Message> T deserialize(byte[] bytes, Closure<T> parse) {
        parse(bytes)
    }

    def register(def serverUrl) {
        log.info("Registering at $serverUrl")
        def regSocket = ctx.socket(ZMQ.REQ)
        regSocket.connect(serverUrl)
        def registration = Registration.newBuilder()
                .setClientType(ClientType.BOT)
                .setId(Id.newBuilder()
                        .setName('Randomizer')
                        .setVersion(1)
                        .build())
                .build()
        def bytes = serialize(registration)
        regSocket.send(bytes, 0)
        RegistrationReply reply = deserialize(regSocket.recv(), RegistrationReply.&parseFrom)
        if (reply.result == RegistrationResult.FAILURE) {
            throw new IllegalStateException("Unable to register for game")
        }
        initSockets(reply)
        gameInfo = reply.gameInfo
        myId = reply.id
    }

    private initSockets(RegistrationReply reply) {
        log.info("Subscribing to ${reply.eventUrl}")
        eventSocket = ctx.socket(ZMQ.SUB)
        eventSocket.subscribe(ZMQ.SUBSCRIPTION_ALL)
        eventSocket.connect(reply.eventUrl)
        log.info("Connecting to ${reply.cmdUrl}")
        cmdSocket = ctx.socket(ZMQ.REQ)
        cmdSocket.connect(reply.cmdUrl)
    }

    def run() {
        while (isAlive) {
            def delay = (1 + this.RANDOM.nextInt(10)) * 50
            log.info("Sleeping for $delay ms")
            sleep(delay)
            if (ready) {
                runSingle()
            }
            handleEvents()
        }
    }

    def handleEvents() {
        def bytes = eventSocket.recv(ZMQ.NOBLOCK)
        while (bytes != null) {
            Event event = deserialize(bytes, Event.&parseFrom)
            switch (event.getEventCase()) {
                case Event.EventCase.DEATH:
                    if (event.death.victim.id == myId) {
                        isAlive = false
                    }
                    break
                case Event.EventCase.SCAN_COMPLETE:
                case Event.EventCase.SHOT_FIRED:
                case Event.EventCase.AIMING_COMPLETE:
                case Event.EventCase.ROTATION_COMPLETE:
                case Event.EventCase.MOVEMENT_COMPLETE:
                    ready = true
                    break
                case Event.EventCase.GAME_OVER:
                    isAlive = false
                    return
            }
            log.info(event.toString())
            bytes = eventSocket.recv(ZMQ.NOBLOCK)
        }
    }

    def runSingle() {
        def values = [
                CommandType.MOVE,
                CommandType.ROTATE,
                CommandType.AIM, CommandType.AIM, CommandType.AIM, CommandType.AIM,
                CommandType.FIRE, CommandType.FIRE, CommandType.FIRE, CommandType.FIRE, CommandType.FIRE, CommandType.FIRE, CommandType.FIRE,
                CommandType.SCAN
        ]
        def nextCmdType = CommandType.forNumber(values[this.RANDOM.nextInt(values.size())].number)
        def nextCmdName = nextCmdType.name()
        log.info("Next cmd is $nextCmdName")
        def nextCmd = Command.newBuilder().setType(nextCmdType)
        switch (nextCmdType) {
            case CommandType.MOVE:
                nextCmd.setValue(this.RANDOM.nextInt(gameInfo.arena.height) as short)
                break
            case CommandType.ROTATE:
                nextCmd.setValue(this.RANDOM.nextInt(270) as short)
                break
            case CommandType.AIM:
                nextCmd.setValue(this.RANDOM.nextInt(270) as short)
                break
            case CommandType.FIRE:
                break
            case CommandType.SCAN:
                nextCmd.setValue(10 as short)
                break
            default:
                throw new IllegalStateException("Picked non-existing command: $nextCmdType")
        }
        log.info("Sending cmd: $nextCmd")
        cmdSocket.send(serialize(nextCmd.build()))
        log.info("Waiting for reply")
        CommandReply reply = deserialize(cmdSocket.recv(), CommandReply.&parseFrom)
        if (reply.getResult() == CommandResult.ACCEPTED) {
            ready = false
        }
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
