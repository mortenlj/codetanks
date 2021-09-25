use std::env;

use anyhow::{anyhow, Result};
use tokio::signal;
use tokio::time::{Duration, sleep};

use crate::domain::command::OptionalValue;

mod domain;
mod comms;

#[tokio::main]
pub async fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    let server_url = args.get(1);

    if server_url.is_none() {
        return Err(anyhow!("You must supply a server url"));
    }

    let server_url = server_url.unwrap();
    let repl = comms::register(server_url).await?;

    let mut commander = comms::Commander::new(&repl).await?;

    sleep(Duration::from_secs(20)).await;

    loop {
        loop {
            if let Ok(()) = commander.command(domain::Command {
                r#type: domain::CommandType::Move as i32,
                optional_value: Some(OptionalValue::Value(20)),
            }).await {
                break;
            };
            sleep(Duration::from_millis(100)).await;
        }

        loop {
            if let Ok(()) = commander.command(domain::Command {
                r#type: domain::CommandType::Rotate as i32,
                optional_value: Some(OptionalValue::Value(10)),
            }).await {
                break;
            }
            sleep(Duration::from_millis(100)).await;
        };

        loop {
            if let Ok(()) = commander.command(domain::Command {
                r#type: domain::CommandType::Aim as i32,
                optional_value: Some(OptionalValue::Value(-5)),
            }).await {
                break;
            }
            sleep(Duration::from_millis(100)).await;
        }

        loop {
            if let Ok(()) = commander.command(domain::Command {
                r#type: domain::CommandType::Fire as i32,
                optional_value: None,
            }).await {
                break;
            }
            sleep(Duration::from_millis(100)).await;
        }
    }

    // match signal::ctrl_c().await {
    //     Ok(()) => {}
    //     Err(err) => {
    //         eprintln!("Unable to listen for shutdown signal: {}", err);
    //         return Err(anyhow!(err));
    //     }
    // }
    // Ok(())
}
