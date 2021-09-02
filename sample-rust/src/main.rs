use std::env;

use bytes::{Bytes};
use prost::{DecodeError, Message};
use tokio::signal;
use zeromq::{BlockingRecv, BlockingSend, ReqSocket, Socket, ZmqMessage};

mod domain;

#[tokio::main]
pub async fn main() -> Result<(), &'static str> {
    let args: Vec<String> = env::args().collect();
    let server_url = args.get(1);
    if server_url.is_none() {
        return Err("You must supply a server url");
    }

    let server_url = server_url.unwrap();
    println!("Registering for {}", server_url);
    let mut req_socket = ReqSocket::new();
    req_socket
        .connect(server_url)
        .await
        .expect("Failed to connect");

    let registration = domain::Registration {
        client_type: domain::ClientType::Bot as i32,
        id: Some(domain::Id {
            name: "Rusty".to_string(),
            version: 1,
        }),
    };

    req_socket
        .send(ZmqMessage::from(registration.encode_to_vec()))
        .await
        .expect("Failed to send registration");


    let repl: domain::RegistrationReply = req_socket
        .recv()
        .await
        .map(zmq_decode)
        .expect("Failed to receive registration reply")
        .expect("Failed to decode registration reply");

    if repl.result() == domain::RegistrationResult::Failure {
        return Result::Err("Unable to register for game");
    }
    dbg!(repl);

    match signal::ctrl_c().await {
        Ok(()) => {}
        Err(err) => {
            eprintln!("Unable to listen for shutdown signal: {}", err);
            // we also shut down in case of error
        }
    }
    Ok({})
}

fn zmq_decode<T: prost::Message + std::default::Default>(zm: ZmqMessage) -> Result<T, DecodeError> {
    let vec = zm.data.to_vec();
    let data = Bytes::from(vec);
    return T::decode(data);
}
