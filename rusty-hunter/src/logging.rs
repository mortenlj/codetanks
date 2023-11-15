use anyhow::Result;
use tracing::info;
use tracing_subscriber::{filter, Registry};
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::prelude::*;

use crate::settings::{AppConfig, LogFormat};

pub fn init_logging(config: &AppConfig) -> Result<()> {
    use tracing_subscriber::fmt as layer_fmt;
    let (plain_log_format, json_log_format) = match config.log_format {
        LogFormat::Plain => (Some(layer_fmt::layer().compact()), None),
        LogFormat::Json => (None, Some(layer_fmt::layer().json().flatten_event(true))),
    };

    Registry::default()
        .with(plain_log_format)
        .with(json_log_format)
        .with(
            filter::Targets::new()
                .with_default(&config.log_level)
        )
        .init();
    info!("{:?} logger initialized", config.log_format);

    Ok(())
}
