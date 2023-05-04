#![warn(missing_docs)]
#![forbid(unsafe_code)]
#![warn(clippy::perf)]
#![warn(clippy::pedantic)]
#![allow(clippy::module_name_repetitions)]
#![doc = include_str!("../README.md")]

use crate::routes::build_application_router;
use crate::service::MyProjectState;
use axum::BoxError;
use settings::MyProjectSettings;
use wai_axum_extra::prelude::*;

/// Contains the domain
pub mod domain;

/// Contains the state, the error, ...
#[macro_use]
pub mod service;

/// Contains the routes
pub mod routes;

/// The clap settings
pub mod settings;

/// Launch the micro service
///
/// # Errors
///
/// May fail if the axum server could not be started
pub async fn launch(settings: MyProjectSettings) -> Result<(), BoxError> {
    // Create the state
    let state = MyProjectState::default();

    // Create the application router
    let router = build_application_router();

    // Launch the server
    run(settings.server, state, router).await?;

    Ok(())
}
