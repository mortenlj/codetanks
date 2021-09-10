use std::env;

use tokio::signal;
use anyhow::{Result, anyhow};

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


    dbg!(repl);

    match signal::ctrl_c().await {
        Ok(()) => {}
        Err(err) => {
            eprintln!("Unable to listen for shutdown signal: {}", err);
            return Err(anyhow!(err))
        }
    }
    Ok(())
}
