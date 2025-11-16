use anyhow::{anyhow, Result};
use euclid::default::Vector2D;
use euclid::Angle;
use tokio::{select, signal};
use tracing::{debug, info, warn};

use crate::domain::command::OptionalValue;
use crate::domain::event::Event;
use crate::domain::{BotStatus, Tank};
use crate::settings::AppConfig;

mod comms;
mod domain;
mod logging;
mod settings;

const SHOTS: i8 = 5;

fn main() -> Result<()> {
    let config = settings::load_config().map_err(|e| anyhow!(e))?;
    app(config)?;
    Ok(())
}

#[derive(Debug, PartialEq)]
struct TargetingSolution {
    aim_angle: Angle<f64>,
    rotate_angle: Angle<f64>,
    distance: i32,
    shots_remaining: i8,
}

impl TargetingSolution {
    fn shoot(self) -> TargetingSolution {
        TargetingSolution {
            distance: self.distance,
            aim_angle: self.aim_angle,
            rotate_angle: self.rotate_angle,
            shots_remaining: self.shots_remaining - 1,
        }
    }
}

#[derive(Debug)]
enum State {
    WaitingForGameStart,
    Searching,
    Firing(TargetingSolution),
    Aiming,
    AimingAtTarget(TargetingSolution),
    Rotating(TargetingSolution),
    Moving,
    Lost,
}

fn make_vector(point: &Option<domain::Point>) -> Result<Vector2D<f64>> {
    match point {
        Some(p) => Ok(Vector2D::new(p.x, p.y)),
        None => Err(anyhow!("point missing")),
    }
}

fn make_targeting_solution(me: &Tank, target: &Tank) -> Result<TargetingSolution> {
    let my_pos = make_vector(&me.position)?;
    let target_pos = make_vector(&target.position)?;
    let vector_to_target = target_pos - my_pos;

    let my_turret = make_vector(&me.turret)?;
    let aim_angle = my_turret.angle_to(vector_to_target);

    let my_heading = make_vector(&me.direction)?;
    let rotate_angle = my_heading.angle_to(vector_to_target);

    let targeting_solution = TargetingSolution {
        aim_angle,
        rotate_angle,
        distance: vector_to_target.length() as i32,
        shots_remaining: SHOTS,
    };
    Ok(targeting_solution)
}

async fn start_searching(commander: &mut comms::Commander, spread: i32) -> Result<State> {
    info!("Starting search with angle spread {}", spread);
    commander
        .command(domain::Command {
            r#type: domain::CommandType::Scan as i32,
            peer_id: None,
            optional_value: Some(OptionalValue::Value(spread)),
        })
        .await?;
    Ok(State::Searching)
}

async fn start_aiming_at_target(
    commander: &mut comms::Commander,
    target: &Tank,
    me: &Tank,
) -> Result<State> {
    let targeting_solution = make_targeting_solution(me, target)?;
    start_aiming_at_angle(commander, targeting_solution.aim_angle.to_degrees() as i32).await?;
    info!("Developed targeting solution: {:?}", targeting_solution);
    Ok(State::AimingAtTarget(targeting_solution))
}

async fn start_aiming_at_angle(commander: &mut comms::Commander, angle: i32) -> Result<State> {
    info!("Adjusting aim by {} degrees", angle);
    commander
        .command(domain::Command {
            r#type: domain::CommandType::Aim as i32,
            peer_id: None,
            optional_value: Some(OptionalValue::Value(angle)),
        })
        .await?;
    Ok(State::Aiming)
}

async fn start_firing(
    commander: &mut comms::Commander,
    targeting_solution: TargetingSolution,
) -> Result<State> {
    if targeting_solution.shots_remaining > 0 {
        info!(
            "Firing cannon according to targeting solution: {:?}",
            targeting_solution
        );
        commander
            .command(domain::Command {
                r#type: domain::CommandType::Fire as i32,
                peer_id: None,
                optional_value: None,
            })
            .await?;
        Ok(State::Firing(targeting_solution.shoot()))
    } else {
        info!(
            "Rotate towards target according to targeting solution: {:?}",
            targeting_solution
        );
        commander
            .command(domain::Command {
                r#type: domain::CommandType::Rotate as i32,
                peer_id: None,
                optional_value: Some(OptionalValue::Value(
                    targeting_solution.rotate_angle.to_degrees() as i32,
                )),
            })
            .await?;
        Ok(State::Rotating(targeting_solution))
    }
}

async fn start_moving(
    commander: &mut comms::Commander,
    targeting_solution: TargetingSolution,
) -> Result<State> {
    info!(
        "Move towards target according to targeting solution: {:?}",
        targeting_solution
    );
    commander
        .command(domain::Command {
            r#type: domain::CommandType::Move as i32,
            peer_id: None,
            optional_value: Some(OptionalValue::Value(targeting_solution.distance * 3 / 4)),
        })
        .await?;
    Ok(State::Moving)
}

fn select_target(tanks: &Vec<Tank>) -> Option<Tank> {
    let live_tanks: Vec<Tank> = tanks
        .iter()
        .map(|t| t.to_owned())
        .filter(|t| t.status != BotStatus::Dead as i32)
        .collect();
    live_tanks.first().map(|t| t.to_owned())
}

fn handle_error(result: Result<State>) -> Result<State> {
    match result {
        Ok(state) => Ok(state),
        Err(e) => {
            if e.to_string().contains("Server busy") {
                info!("Server busy, retrying...");
                return Ok(State::Lost);
            }
            Err(e)
        }
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
                                State::Lost => {
                                    handle_error(start_searching(&mut commander, 20).await)?
                                }
                                State::WaitingForGameStart => {
                                    match inner {
                                        Event::GameStarted(_) => {
                                            handle_error(start_searching(&mut commander, 20).await)?
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
                                            if let Some(target) = select_target(&scan_complete.tanks) {
                                                handle_error(start_aiming_at_target(&mut commander, &target, &me).await)?
                                            } else {
                                                handle_error(start_aiming_at_angle(&mut commander, 20).await)?
                                            }
                                        },
                                        _ => {
                                            State::Searching
                                        },
                                    }
                                },
                                State::Firing(targeting_solution) => {
                                    match inner {
                                        Event::ShotFired(_) => {
                                            handle_error(start_firing(&mut commander, targeting_solution).await)?
                                        }
                                        _ => {
                                            State::Firing(targeting_solution)
                                        },
                                    }
                                },
                                State::Aiming => {
                                    match inner {
                                        Event::AimingComplete(_) => {
                                            handle_error(start_searching(&mut commander, 10).await)?
                                        }
                                        _ => {
                                            State::Aiming
                                        },
                                    }
                                }
                                State::AimingAtTarget(targeting_solution) => {
                                    match inner {
                                        Event::AimingComplete(_) => {
                                            handle_error(start_firing(&mut commander, targeting_solution).await)?
                                        }
                                        _ => {
                                            State::AimingAtTarget(targeting_solution)
                                        },
                                    }
                                },
                                State::Rotating(targeting_solution) => {
                                    match inner {
                                        Event::RotationComplete(_) => {
                                            handle_error(start_moving(&mut commander, targeting_solution).await)?
                                        }
                                        _ => {
                                            State::Rotating(targeting_solution)
                                        },
                                    }
                                },
                                State::Moving => {
                                    match inner {
                                        Event::MovementComplete(_) => {
                                            handle_error(start_searching(&mut commander, 40).await)?
                                        }
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

#[cfg(test)]
mod tests {
    use assertables::assert_in_delta;
    use pretty_assertions::assert_eq;
    use rstest::*;

    use crate::domain::{BotStatus, Id, Point, Tank};

    use super::*;

    #[fixture]
    fn me() -> Tank {
        Tank {
            id: 1,
            bot_id: Some(Id {
                name: "me".to_string(),
                version: 1,
            }),
            position: Some(Point { x: 1.0, y: 1.0 }),
            direction: Some(Point { x: 1.0, y: 0.0 }),
            turret: Some(Point { x: -1.0, y: 0.0 }),
            health: 100,
            status: BotStatus::Idle as i32,
        }
    }

    #[rstest]
    #[case::right(Point {x:2.0, y:1.0}, 180.0, 0.0, 1)]
    #[case::left(Point {x:0.0, y:1.0}, 0.0, 180.0, 1)]
    #[case::down(Point {x:1.0, y:2.0}, -90.0, 90.0, 1)]
    #[case::up(Point {x:1.0, y:0.0}, 90.0, -90.0, 1)]
    #[case::down_right(Point {x:2.0, y:2.0}, -135.0, 45.0, 1)]
    fn targeting_solution(
        me: Tank,
        #[case] position: Point,
        #[case] aim_angle: f64,
        #[case] rotate_angle: f64,
        #[case] distance: i32,
    ) {
        let target = Tank {
            id: 2,
            bot_id: Some(Id {
                name: "target".to_string(),
                version: 1,
            }),
            position: Some(position),
            direction: Some(Point { x: 0.0, y: 0.0 }),
            turret: Some(Point { x: 0.0, y: 0.0 }),
            health: 100,
            status: BotStatus::Idle as i32,
        };
        let solution = make_targeting_solution(&me, &target).unwrap();
        assert_eq!(solution.distance, distance);
        assert_in_delta!(solution.aim_angle.to_degrees(), aim_angle, 0.05);
        assert_in_delta!(solution.rotate_angle.to_degrees(), rotate_angle, 0.05);
    }
    #[rstest]
    fn real_world() {
        let me = Tank {
            id: 0,
            bot_id: Some(Id {
                name: "Rusty".to_string(),
                version: 1,
            }),
            position: Some(Point {
                x: 387.78719262470514,
                y: 483.7131060564801,
            }),
            direction: Some(Point {
                x: 0.8290375725550414,
                y: 0.5591929034707472,
            }),
            turret: Some(Point {
                x: 0.3907311284892584,
                y: -0.9205048534524469,
            }),
            health: 90,
            status: BotStatus::Idle as i32,
        };
        let target = Tank {
            id: 2,
            bot_id: Some(Id {
                name: "Randomizer".to_string(),
                version: 1,
            }),
            position: Some(Point {
                x: 482.9819551078393,
                y: 325.53912985056326,
            }),
            direction: Some(Point {
                x: 0.017452406437283408,
                y: 0.9998476951563913,
            }),
            turret: Some(Point {
                x: -0.29237170472273505,
                y: 0.9563047559630361,
            }),
            health: 70,
            status: BotStatus::Idle as i32,
        };
        let solution = make_targeting_solution(&me, &target).unwrap();
        assert_in_delta!(solution.aim_angle.to_degrees(), 0.0, 11.0);
    }
}
