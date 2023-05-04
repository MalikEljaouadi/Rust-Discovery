use assert2::{check, let_assert};
use axum::http::StatusCode;
use my_project::routes::build_application_router;
use my_project::service::MyProjectState;
use once_cell::sync::Lazy;
use wai_axum_extra::prelude::HealthCheckStatus;
use wai_axum_extra::service::health::HealthStatus;
use wai_axum_extra::service::ApiError;
use wai_axum_extra_test::{TestApp, INIT_TRACING};

const APP_NAME: &str = "my_project";

async fn build_test_app() -> TestApp {
    std::env::set_var("APP_NAME", APP_NAME);
    Lazy::force(&INIT_TRACING);
    let state = MyProjectState::default();
    let router = build_application_router();
    TestApp::start(state, router).await
}

#[tokio::test]
async fn should_have_healthcheck_endpoint() {
    let app = build_test_app().await;

    let result = app.get_json::<HealthCheckStatus>("/health").await;

    let_assert!(Ok(status) = result);
    check!(status.status == HealthStatus::Up);
}

#[tokio::test]
async fn should_have_no_trace_header_on_health() {
    let app = build_test_app().await;

    let response = app.get_raw("/health").await;
    let headers = response.headers();

    check!(!headers.contains_key("Traceparent"));
    check!(!headers.contains_key("Tracestate"));
}

#[tokio::test]
async fn should_have_correlation_id_on_standard_route() {
    let app = build_test_app().await;

    let response = app.get_raw("/").await;
    let headers = response.headers();

    check!(headers.contains_key("Traceparent"));
    check!(headers.contains_key("Tracestate"));
}

#[tokio::test]
async fn should_have_correlation_id_on_not_found() {
    let app = build_test_app().await;

    let response = app.get_raw("/plaf").await;
    let headers = response.headers().clone();
    let status = response.status();

    check!(status == StatusCode::NOT_FOUND);
    check!(headers.contains_key("Traceparent"));
    check!(headers.contains_key("Tracestate"));

    let_assert!(Ok(error) = response.json::<ApiError>().await);
    check!(error.source == APP_NAME);
    let_assert!(Some(trace_id) = error.correlation_id);
    let_assert!(Ok(s) = headers["Traceparent"].to_str());
    let id = s.split('-').nth(1).unwrap_or_default();
    check!(id == trace_id);
}
