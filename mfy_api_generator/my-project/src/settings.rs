use clap::Parser;
use wai_axum_extra::prelude::*;

/// `my-project` application CLI arguments
#[derive(Debug, Clone, Parser)]
pub struct MyProjectSettings {
    /// The server configuration
    #[clap(flatten)]
    pub server: ServerSettings,
    // Other settings ...
}
