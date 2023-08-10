use anyhow::{anyhow, Result};
use tokio::time::{Duration, sleep};
use tracing::{debug, info};
use tracing::field::debug;

use crate::settings::AppConfig;

use crate::domain::command::OptionalValue;

mod domain;
mod comms;
mod settings;
mod logging;

fn main() -> Result<()> {
    let config = settings::load_config().map_err(|e| anyhow!(e))?;
    app(config)?;
    Ok(())
}

#[tokio::main]
async fn app(config: AppConfig) -> Result<()> {
    logging::init_logging(&config)?;
    info!("Configuration loaded: {:?}", config);

    let repl = comms::register(&config.server_uri).await?;

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
            debug!("Moving 20 clicks forward");
            sleep(Duration::from_millis(100)).await;
        }

        loop {
            if let Ok(()) = commander.command(domain::Command {
                r#type: domain::CommandType::Rotate as i32,
                optional_value: Some(OptionalValue::Value(10)),
            }).await {
                break;
            }
            debug!("Rotating 10 degrees");
            sleep(Duration::from_millis(100)).await;
        };

        loop {
            if let Ok(()) = commander.command(domain::Command {
                r#type: domain::CommandType::Aim as i32,
                optional_value: Some(OptionalValue::Value(-5)),
            }).await {
                break;
            }
            debug!("Aiming -5 degrees");
            sleep(Duration::from_millis(100)).await;
        }

        loop {
            if let Ok(()) = commander.command(domain::Command {
                r#type: domain::CommandType::Fire as i32,
                optional_value: None,
            }).await {
                break;
            }
            debug!("FIRE!");
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
