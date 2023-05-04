use axum::Router;

use crate::service::MyProjectState;

/// This is the application router
pub fn build_application_router() -> Router<MyProjectState> {
    Router::new().nest("/ai/my-project", Router::new())
}
