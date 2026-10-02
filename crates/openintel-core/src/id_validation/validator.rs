use rayon::prelude::*;
use serde::{Deserialize, Serialize};

use crate::id_validation::schemes::{
    validate_br_cpf, validate_es_dni, validate_es_nie, validate_fr_nif, validate_it_codice_fiscale,
    validate_mx_curp, validate_us_ssn,
};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ValidationResult {
    pub scheme: String,
    pub country: String,
    pub standard: String,
}

/// Validate a single national ID against supported international registries.
pub fn validate_single(raw_id: &str) -> Vec<ValidationResult> {
    let mut matches = Vec::new();
    let trimmed = raw_id.trim();

    // 1. Spain DNI
    if let Some(standard) = validate_es_dni(trimmed) {
        matches.push(ValidationResult {
            scheme: "Spain DNI".to_string(),
            country: "ESP".to_string(),
            standard,
        });
    }

    // 2. Spain NIE
    if let Some(standard) = validate_es_nie(trimmed) {
        matches.push(ValidationResult {
            scheme: "Spain NIE".to_string(),
            country: "ESP".to_string(),
            standard,
        });
    }

    // 3. Brazil CPF
    if let Some(standard) = validate_br_cpf(trimmed) {
        matches.push(ValidationResult {
            scheme: "Brazil CPF".to_string(),
            country: "BRA".to_string(),
            standard,
        });
    }

    // 4. USA SSN
    if let Some(standard) = validate_us_ssn(trimmed) {
        matches.push(ValidationResult {
            scheme: "USA SSN".to_string(),
            country: "USA".to_string(),
            standard,
        });
    }

    // 5. Mexico CURP
    if let Some(standard) = validate_mx_curp(trimmed) {
        matches.push(ValidationResult {
            scheme: "Mexico CURP".to_string(),
            country: "MEX".to_string(),
            standard,
        });
    }

    // 6. France NIF
    if let Some(standard) = validate_fr_nif(trimmed) {
        matches.push(ValidationResult {
            scheme: "France NIF".to_string(),
            country: "FRA".to_string(),
            standard,
        });
    }

    // 7. Italy Codice Fiscale
    if let Some(standard) = validate_it_codice_fiscale(trimmed) {
        matches.push(ValidationResult {
            scheme: "Italy Codice Fiscale".to_string(),
            country: "ITA".to_string(),
            standard,
        });
    }

    matches
}

/// Validate a batch of national IDs concurrently using Rayon work-stealing threads.
pub fn validate_batch(raw_ids: &[String]) -> Vec<Vec<ValidationResult>> {
    raw_ids.par_iter().map(|id| validate_single(id)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_es_dni() {
        // 12345678Z is a classic valid DNI
        let res = validate_single("12345678Z");
        assert_eq!(res.len(), 1);
        assert_eq!(res[0].scheme, "Spain DNI");
        assert_eq!(res[0].country, "ESP");
    }

    #[test]
    fn test_valid_br_cpf() {
        // Valid CPF example
        let res = validate_single("11144477735");
        assert_eq!(res.len(), 1);
        assert_eq!(res[0].scheme, "Brazil CPF");
        assert_eq!(res[0].country, "BRA");
    }

    #[test]
    fn test_batch_validation() {
        let ids = vec![
            "12345678Z".to_string(),
            "11144477735".to_string(),
            "invalid_id_999".to_string(),
        ];
        let batch_res = validate_batch(&ids);
        assert_eq!(batch_res.len(), 3);
        assert_eq!(batch_res[0].len(), 1);
        assert_eq!(batch_res[1].len(), 1);
        assert_eq!(batch_res[2].len(), 0);
    }
}
