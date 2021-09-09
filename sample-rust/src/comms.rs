use anyhow::{Context, Result, anyhow};
use bytes::Bytes;
use prost::{DecodeError, Message};
use thiserror::Error;
use zeromq::{BlockingRecv, BlockingSend, ReqSocket, Socket, ZmqMessage};

use crate::domain::{ClientType, Id, Registration, RegistrationReply, RegistrationResult};

#[derive(Error, Debug)]
pub enum CommsError {
    #[error("Server refused our registration")]
    RegistrationFailure,
}

pub async fn register(server_url: &String) -> Result<RegistrationReply, anyhow::Error> {
    println!("Registering for {}", server_url);
    let mut req_socket = ReqSocket::new();
    req_socket
        .connect(server_url)
        .await
        .context("failed to connect")?;

    let registration = Registration {
        client_type: ClientType::Bot as i32,
        id: Some(Id {
            name: "Rusty".to_string(),
            version: 1,
        }),
    };

    req_socket
        .send(ZmqMessage::from(registration.encode_to_vec()))
        .await
        .context("Failed to send registration")?;


    let repl: RegistrationReply = req_socket
        .recv()
        .await
        .map(zmq_decode)
        .context("Failed to receive registration reply")?
        .context("Failed to decode registration reply")?;

    if repl.result() == RegistrationResult::Failure {
        return Err(anyhow!(CommsError::RegistrationFailure))
    }

    Ok(repl)
}

fn zmq_decode<T: prost::Message + std::default::Default>(zm: ZmqMessage) -> Result<T, DecodeError> {
    let vec = zm.data.to_vec();
    let data = Bytes::from(vec);
    return T::decode(data);
}
