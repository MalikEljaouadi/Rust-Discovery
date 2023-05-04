use axum::BoxError;
use clap::Parser;
use my_project::launch;
use my_project::settings::MyProjectSettings;
use wai_axum_extra::prelude::*;

/// Run the server with a Tokio runtime
#[tokio::main]
async fn main() -> Result<(), BoxError> {
    // Initialize the tracing
    init_tracing()?;

    // Parsing args
    let settings = MyProjectSettings::parse();

    // Let's go
    launch(settings).await
}
