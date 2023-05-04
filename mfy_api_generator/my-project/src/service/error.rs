use wai_axum_extra::prelude::*;

/// The application level error
#[derive(thiserror::Error, Debug, Clone, ApplicationError)]
pub enum MyProjectError {
    // TODO add your errors
}
