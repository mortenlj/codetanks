use anyhow::{anyhow, Context, Result};
use thiserror::Error;
use tracing::{debug, info};
use zeromq::{ReqSocket, Socket, SocketRecv, SocketSend, SubSocket, ZmqMessage};

use crate::domain::{ClientType, Command, CommandReply, CommandResult, Id, Registration, RegistrationReply, RegistrationResult};

#[derive(Error, Debug)]
pub enum CommsError {
    #[error("Server refused our registration")]
    RegistrationFailure,
}

pub struct Commander {
    pub cmd_socket: ReqSocket,
    pub event_socket: SubSocket,
}

impl Commander {
    pub async fn new(registration: &RegistrationReply) -> Result<Commander> {
        let mut cmd_socket = ReqSocket::new();
        cmd_socket
            .connect(registration.cmd_url.as_str())
            .await
            .context("Failed to connect to command socket")?;

        let mut event_socket = SubSocket::new();
        event_socket
            .connect(registration.event_url.as_str())
            .await
            .context("Failed to connect to event socket")?;

        let commander = Commander {
            cmd_socket,
            event_socket,
        };
        Ok(commander)
    }

    pub async fn command(&mut self, command: Command) -> Result<()> {
        debug!("Sending command {:?}", &command);

        self.cmd_socket
            .send(zmq_encode(command))
            .await
            .context("Failed to send command")?;
        let repl: CommandReply = self.cmd_socket
            .recv()
            .await
            .map(zmq_decode)
            .context("Failed to receive command reply")?
            .context("Failed to decode command reply")?;

        if repl.result() == CommandResult::Busy {
            return Err(anyhow!("Server busy"));
        } else if repl.result() == CommandResult::Accepted {
            debug!("Command accepted");
        }

        Ok(())
    }
}

pub async fn register(server_url: &String) -> Result<RegistrationReply> {
    info!("Registering for {}", server_url);
    let mut req_socket = ReqSocket::new();
    req_socket
        .connect(server_url)
        .await
        .context("failed to connect for registration")?;

    let registration = Registration {
        client_type: ClientType::Bot as i32,
        id: Some(Id {
            name: "Rusty".to_string(),
            version: 1,
        }),
    };

    req_socket
        .send(zmq_encode(registration))
        .await
        .context("Failed to send registration")?;

    let repl: RegistrationReply = req_socket
        .recv()
        .await
        .map(zmq_decode)
        .context("Failed to receive registration reply")?
        .context("Failed to decode registration reply")?;

    if repl.result() == RegistrationResult::Failure {
        return Err(anyhow!(CommsError::RegistrationFailure));
    }

    Ok(repl)
}

fn zmq_decode<T: prost::Message + Default>(zm: ZmqMessage) -> Result<T> {
    let vec = zm.into_vec();
    debug!("Received {} frames of bytes", vec.len());
    let data = vec.get(0).context("No data in message")?.to_owned();
    return T::decode(data).map_err(|e| anyhow!(e));
}

fn zmq_encode<T: prost::Message>(t: T) -> ZmqMessage {
    let zm = ZmqMessage::from(t.encode_to_vec());
    zm
}