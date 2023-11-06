use anyhow::{anyhow, Result};
use euclid::Angle;
use euclid::default::Vector2D;
use tokio::{select, signal};
use tracing::{debug, info, warn};

use crate::domain::command::OptionalValue;
use crate::domain::event::Event;
use crate::settings::AppConfig;

mod domain;
mod comms;
mod settings;
mod logging;

const SHOTS: i8 = 5;

fn main() -> Result<()> {
    let config = settings::load_config().map_err(|e| anyhow!(e))?;
    app(config)?;
    Ok(())
}


#[derive(Debug)]
struct TargetingSolution {
    angle: Angle<f64>,
    distance: i32,
    shots_remaining: i8,
}

impl TargetingSolution {
    fn shoot(self) -> TargetingSolution {
        TargetingSolution {
            distance: self.distance,
            angle: self.angle,
            shots_remaining: self.shots_remaining - 1
        }
    }
}

#[derive(Debug)]
enum State {
    WaitingForGameStart,
    Searching,
    SearchingNarrow,
    Firing(TargetingSolution),
    Aiming,
    AimingAtTarget(TargetingSolution),
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
    let distance_to_target = my_pos.to_point().distance_to(target_pos.to_point()) as i32;
    let target_angle = my_pos.angle_to(target_pos);
    let my_aim = make_vector(&me.turret)?;
    let aim_change = my_aim.angle_from_x_axis() - target_angle;
    start_aiming_at_angle(commander, aim_change.to_degrees() as i32).await?;
    let targeting_solution = TargetingSolution {
        angle: target_angle,
        distance: distance_to_target,
        shots_remaining: SHOTS,
    };
    info!("Developed targeting solution: {:?}", targeting_solution);
    Ok(State::AimingAtTarget(targeting_solution))
}

async fn start_aiming_at_angle(commander: &mut comms::Commander, angle: i32) -> Result<State> {
    info!("Adjusting aim by {} degrees", angle);
    commander.command(domain::Command {
        r#type: domain::CommandType::Aim as i32,
        optional_value: Some(OptionalValue::Value(angle)),
    }).await?;
    Ok(State::Aiming)
}

async fn start_firing(commander: &mut comms::Commander, targeting_solution: TargetingSolution) -> Result<State> {
    if targeting_solution.shots_remaining > 0 {
        info!("Firing cannon according to targeting solution: {:?}", targeting_solution);
        commander.command(domain::Command {
            r#type: domain::CommandType::Fire as i32,
            optional_value: None,
        }).await?;
        Ok(State::Firing(targeting_solution.shoot()))
    } else {
        info!("Move towards target according to targeting solution: {:?}", targeting_solution);
        commander.command(domain::Command {
            r#type: domain::CommandType::Move as i32,
            optional_value: Some(OptionalValue::Value(3 * targeting_solution.distance / 4))
        }).await?;
        Ok(State::Moving)
    }
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
                        debug!("Received event {:?}", event);
                        if let Some(inner) = &event.event {
                            if let Event::GameOver(game_over) = inner {
                                info!("Game Over! Winner was {:?}", game_over.winner.to_owned().unwrap());
                                return Ok(())
                            }
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
                                State::Firing(targeting_solution) => {
                                    match inner {
                                        Event::ShotFired(_) => {
                                            start_firing(&mut commander, targeting_solution).await?
                                        }
                                        _ => {
                                            State::Firing(targeting_solution)
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
                                State::AimingAtTarget(targeting_solution) => {
                                    match inner {
                                        Event::AimingComplete(_) => {
                                            start_firing(&mut commander, targeting_solution).await?
                                        }
                                        _ => {
                                            State::AimingAtTarget(targeting_solution)
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
