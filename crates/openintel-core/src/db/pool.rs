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
    let schema_sql = match std::fs::read_to_string("openintel.sql") {
        Ok(sql) => sql,
        Err(_) => match std::fs::read_to_string("../../openintel.sql") {
            Ok(sql) => sql,
            Err(e) => {
                return Err(DbError::MigrationError(format!(
                    "Failed to read openintel.sql: {}",
                    e
                )))
            }
        },
    };

    sqlx::raw_sql(&schema_sql)
        .execute(pool)
        .await
        .map_err(|e| DbError::MigrationError(e.to_string()))?;

    Ok(())
}
