use sqlx::postgres::{PgPool, PgPoolOptions};
use std::time::Duration;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum DbError {
    #[error("PostgreSQL connection error: {0}")]
    ConnectionError(#[from] sqlx::Error),
    #[error("Database migration error: {0}")]
    MigrationError(String),
}

/// Creates a tuned PostgreSQL connection pool.
/// Enforces PostgreSQL only - zero SQLite dependencies.
pub async fn create_pg_pool(database_url: &str, max_connections: u32) -> Result<PgPool, DbError> {
    let pool = PgPoolOptions::new()
        .max_connections(max_connections)
        .min_connections(2)
        .acquire_timeout(Duration::from_secs(5))
        .idle_timeout(Duration::from_secs(600))
        .max_lifetime(Duration::from_secs(1800))
        .connect(database_url)
        .await?;

    Ok(pool)
}

/// Runs PostgreSQL database schema initialization.
pub async fn run_migrations(pool: &PgPool) -> Result<(), DbError> {
    let candidate_paths = [
        "openintel.sql",
        "../../openintel.sql",
        "examples/openintel_schema_example.sql",
        "../../examples/openintel_schema_example.sql",
    ];

    let mut schema_sql = None;
    for path in candidate_paths {
        if let Ok(sql) = std::fs::read_to_string(path) {
            schema_sql = Some(sql);
            break;
        }
    }

    let schema_sql = match schema_sql {
        Some(sql) => sql,
        None => {
            return Err(DbError::MigrationError(
                "Failed to find schema file (checked openintel.sql and examples/openintel_schema_example.sql)".to_string(),
            ))
        }
    };

    sqlx::raw_sql(&schema_sql)
        .execute(pool)
        .await
        .map_err(|e| DbError::MigrationError(e.to_string()))?;

    Ok(())
}
