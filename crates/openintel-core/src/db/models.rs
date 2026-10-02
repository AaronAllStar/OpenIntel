use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct InvestigationRecord {
    pub id: Uuid,
    pub name: String,
    pub target_kind: String,
    pub target_value: String,
    pub investigation_type: String,
    pub status: String,
    pub created_at: DateTime<Utc>,
    pub started_at: Option<DateTime<Utc>>,
    pub finished_at: Option<DateTime<Utc>>,
    pub created_by: Uuid,
    pub error_message: Option<String>,
    pub settings: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct EntityRecord {
    pub id: Uuid,
    pub investigation_id: Uuid,
    pub kind: String,
    pub value: String,
    pub canonical_key: String,
    pub confidence: String,
    pub attributes: serde_json::Value,
    pub first_seen: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct RelationshipRecord {
    pub id: Uuid,
    pub investigation_id: Uuid,
    pub source_entity_id: Uuid,
    pub target_entity_id: Uuid,
    pub predicate: String,
    pub confidence: String,
    pub reasoning: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct EvidenceRecord {
    pub id: Uuid,
    pub investigation_id: Uuid,
    pub entity_id: Option<Uuid>,
    pub relationship_id: Option<Uuid>,
    pub source: String,
    pub tool: String,
    pub raw_observation: String,
    pub confidence: String,
    pub info_classification: String,
    pub timestamp: DateTime<Utc>,
    pub metadata: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct AuditLogRecord {
    pub id: Uuid,
    pub timestamp: DateTime<Utc>,
    pub user_id: String,
    pub role: String,
    pub action: String,
    pub resource_type: String,
    pub resource_id: String,
    pub ip_address: String,
    pub status: String,
    pub details_json: serde_json::Value,
}
