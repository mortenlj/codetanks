use anyhow::{anyhow, Result};
use tokio::{select, signal};
use tracing::{info, warn};
use crate::domain::event::Event;

use crate::settings::AppConfig;

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

    loop {
        select! {
            Ok(_) = signal::ctrl_c() => {
                info!("Received quit signal");
                break;
            }
            maybe_event = commander.next_event() => {
                match &maybe_event {
                    Ok(event) => {
                        info!("Received event {:?}", event);
                        if let Some(inner) = &event.event {
                            info!("Received inner event {:?}", inner);
                            match inner {
                                Event::Scan(scan_result) => {
                                    info!("Scan result: {:?}", scan_result);
                                },
                                Event::Death(death) => {
                                    info!("Death: {:?}", death);
                                },
                                Event::Result(command_result) => {
                                    info!("Command result: {:?}", command_result);
                                },
                                Event::GameStarted(game_started) => {
                                    info!("Game started: {:?}", game_started);
                                },
                                Event::GameOver(game_over) => {
                                    info!("Game over: {:?}", game_over);
                                },
                                Event::GameData(game_data) => {
                                    info!("Game data: {:?}", game_data);
                                },
                            }
                        }
                    },
                    Err(e) => {
                        warn!("Failed to receive event: {:?}", e);
                    },
                }
            }
        }
    }
    Ok(())
}
