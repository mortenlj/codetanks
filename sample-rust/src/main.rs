use anyhow::{anyhow, Result};
use euclid::default::Vector2D;
use tokio::{select, signal};
use tracing::{info, warn};

use crate::domain::command::OptionalValue;
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


#[derive(Debug)]
enum State {
    WaitingForGameStart,
    Searching,
    SearchingNarrow,
    Firing1,
    Firing2,
    Aiming,
    AimingAtTarget,
    Rotating,
    RotatingToHunt,
    Moving,
}

async fn start_searching(commander: &mut comms::Commander, angle: i32) -> Result<State> {
    info!("Starting search with angle spread {}", angle);
    commander.command(domain::Command {
        r#type: domain::CommandType::Scan as i32,
        optional_value: Some(OptionalValue::Value(angle)),
    }).await?;
    Ok(State::Searching)
}


fn make_vector(point: &Option<domain::Point>) -> Result<Vector2D<f64>> {
    match point {
        Some(p) => {
            Ok(Vector2D::new(p.x, p.y))
        }
        None => {
            Err(anyhow!("point missing"))
        }
    }
}

async fn start_aiming_at_target(commander: &mut comms::Commander, target: &domain::Tank, me: &domain::Tank) -> Result<State> {
    let my_pos = make_vector(&me.position)?;
    let target_pos = make_vector(&target.position)?;
    let target_angle = my_pos.angle_to(target_pos);
    let my_aim = make_vector(&me.turret)?;
    let aim_change = my_aim.angle_from_x_axis() - target_angle;
    start_aiming_at_angle(commander, aim_change.to_degrees() as i32).await?;
    Ok(State::AimingAtTarget)
}

async fn start_aiming_at_angle(commander: &mut comms::Commander, angle: i32) -> Result<State> {
    info!("Adjusting aim by {} degrees", angle);
    commander.command(domain::Command {
        r#type: domain::CommandType::Aim as i32,
        optional_value: Some(OptionalValue::Value(angle)),
    }).await?;
    Ok(State::Aiming)
}

async fn start_firing(commander: &mut comms::Commander) -> Result<State> {
    info!("FIRE!");
    commander.command(domain::Command {
        r#type: domain::CommandType::Fire as i32,
        optional_value: None,
    }).await?;
    Ok(State::Firing1)
}

#[tokio::main]
async fn app(config: AppConfig) -> Result<()> {
    logging::init_logging(&config)?;
    info!("Configuration loaded: {:?}", config);

    let repl = comms::register(&config.server_uri).await?;

    let mut commander = comms::Commander::new(&repl).await?;
    let mut current_state = State::WaitingForGameStart;

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
                            info!("Received inner event {:?} while in state {:?}", inner, current_state);
                            current_state = match current_state {
                                State::WaitingForGameStart => {
                                    match inner {
                                        Event::GameStarted(_) => {
                                            start_searching(&mut commander, 20).await?
                                        },
                                        _ => {
                                            State::WaitingForGameStart
                                        },
                                    }
                                },
                                State::Searching => {
                                    match inner {
                                        Event::ScanComplete(scan_complete) => {
                                            let me = scan_complete.you.to_owned().unwrap();
                                            if scan_complete.tanks.len() > 0 {
                                                let target = scan_complete.tanks[0].to_owned();
                                                start_aiming_at_target(&mut commander, &target, &me).await?
                                            } else {
                                                start_aiming_at_angle(&mut commander, 20).await?
                                            }
                                        },
                                        _ => {
                                            State::Searching
                                        },
                                    }
                                },
                                State::SearchingNarrow => {
                                    match inner {
                                        _ => {
                                            State::SearchingNarrow
                                        },
                                    }
                                },
                                State::Firing1 => {
                                    match inner {
                                        Event::ShotFired(_) => {
                                            start_firing(&mut commander).await?
                                        }
                                        _ => {
                                            State::Firing1
                                        },
                                    }
                                },
                                State::Firing2 => {
                                    match inner {
                                        _ => {
                                            State::Firing2
                                        },
                                    }
                                },
                                State::Aiming => {
                                    match inner {
                                        Event::AimingComplete(_) => {
                                            start_searching(&mut commander, 20).await?
                                        }
                                        _ => {
                                            State::Aiming
                                        },
                                    }
                                }
                                State::AimingAtTarget => {
                                    match inner {
                                        Event::AimingComplete(_) => {
                                            start_firing(&mut commander).await?
                                        }
                                        _ => {
                                            State::AimingAtTarget
                                        },
                                    }
                                },
                                State::Rotating => {
                                    match inner {
                                        _ => {
                                            State::Rotating
                                        },
                                    }
                                },
                                State::RotatingToHunt => {
                                    match inner {
                                        _ => {
                                            State::RotatingToHunt
                                        },
                                    }
                                },
                                State::Moving => {
                                    match inner {
                                        _ => {
                                            State::Moving
                                        },
                                    }
                                },
                            };
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
