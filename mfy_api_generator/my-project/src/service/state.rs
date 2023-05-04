use time::OffsetDateTime;
use wai_axum_extra::prelude::*;

use super::MyProjectError;

/// Defining the application Axum state
#[derive(Debug, Clone)]
pub struct MyProjectState {
    start_time: OffsetDateTime,
}

/// Should provide the health check
#[axum::async_trait]
impl ApplicationState<MyProjectError> for MyProjectState {
    async fn check_health_status(&self) -> Result<HealthCheckStatus, MyProjectError> {
        let version = env!("CARGO_PKG_VERSION");
        Ok(HealthCheckStatus::up(version, self.start_time))
    }
}

/// Just a way to create the state
impl Default for MyProjectState {
    fn default() -> Self {
        Self {
            start_time: OffsetDateTime::now_utc(),
        }
    }
}
