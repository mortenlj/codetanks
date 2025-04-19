use schematic::{Config, ConfigEnum, ConfigLoader};
use serde::{Deserialize, Serialize};
use std::io::IsTerminal;
use tracing::level_filters::LevelFilter;

#[derive(ConfigEnum, Debug, Deserialize, Serialize, Clone, PartialEq, Eq)]
pub enum LogFormat {
    Plain,
    Json,
}

impl Default for LogFormat {
    fn default() -> Self {
        match std::io::stdout().is_terminal() {
            true => LogFormat::Plain,
            false => LogFormat::Json,
        }
    }
}

#[derive(ConfigEnum, Debug, Default, Deserialize, Serialize, Clone, PartialEq, Eq)]
pub enum LogLevel {
    Trace = 0,
    Debug = 1,
    #[default]
    Info = 2,
    Warn = 3,
    Error_ = 4,
}

impl Into<LevelFilter> for &LogLevel {
    fn into(self) -> LevelFilter {
        match self {
            LogLevel::Trace => LevelFilter::TRACE,
            LogLevel::Debug => LevelFilter::DEBUG,
            LogLevel::Info => LevelFilter::INFO,
            LogLevel::Warn => LevelFilter::WARN,
            LogLevel::Error_ => LevelFilter::ERROR,
        }
    }
}

#[derive(Config, Debug, Deserialize, Serialize, Clone)]
#[config(env_prefix = "")]
pub struct AppConfig {
    // Logging format to use
    #[serde(default)]
    #[setting]
    pub log_format: LogFormat,
    // Log level
    #[serde(default)]
    #[setting]
    pub log_level: LogLevel,
    // Server URI
    #[setting(validate = schematic::validate::regex("tcp://.*"))]
    pub server_uri: String
}

pub fn load_config() -> anyhow::Result<AppConfig> {
    let config_load_result = ConfigLoader::<AppConfig>::new().load()?;
    Ok(config_load_result.config)
}

#[cfg(test)]
mod tests {
    use super::*;
    use envtestkit::lock::lock_test;
    use envtestkit::set_env;
    use pretty_assertions::assert_eq;
    use rstest::*;
    use std::ffi::OsString;

    const SERVER_URI: &'static str = "tcp://127.0.0.1:13337";
    const SERVER_URI_KEY: &'static str = "SAMPLE_RUST__SERVER_URI";

    #[rstest]
    #[case::server_uri(SERVER_URI_KEY, SERVER_URI, SERVER_URI)]
    pub fn test_load_config(#[case] key: &str, #[case] expected: &str, #[case] value: &str) {
        let _lock = lock_test();
        let _guard = set_env(OsString::from(key), value);

        let config = load_config().unwrap();

        match key {
            SERVER_URI_KEY => {
                assert_eq!(config.server_uri, expected)
            },
            _ => {
                panic!("Unmatched configuration key in test")
            },
        }
    }

    #[rstest]
    #[should_panic]
    pub fn test_required_fields() {
        let _lock = lock_test();

        let _config = load_config().unwrap();
    }
}
