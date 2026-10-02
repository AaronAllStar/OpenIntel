use crate::id_validation::algorithms::compute_mod11;

/// Spain DNI: 8 digits + control letter (Modulo 23).
pub fn validate_es_dni(raw: &str) -> Option<String> {
    let clean: String = raw.chars().filter(|c| c.is_alphanumeric()).collect();
    if clean.len() != 9 {
        return None;
    }

    let digits_part = &clean[..8];
    let letter_part = clean.chars().nth(8)?.to_ascii_uppercase();

    let num: u64 = digits_part.parse().ok()?;
    const DNI_LETTERS: &[u8] = b"TRWAGMYFPDXBNJZSQVHLCKE";
    let expected = DNI_LETTERS[(num % 23) as usize] as char;

    if letter_part == expected {
        Some(format!("{:08}{}", num, expected))
    } else {
        None
    }
}

/// Spain NIE: Prefix X/Y/Z + 7 digits + control letter.
pub fn validate_es_nie(raw: &str) -> Option<String> {
    let clean: String = raw.chars().filter(|c| c.is_alphanumeric()).collect();
    if clean.len() != 9 {
        return None;
    }

    let first = clean.chars().next()?.to_ascii_uppercase();
    let prefix_val = match first {
        'X' => "0",
        'Y' => "1",
        'Z' => "2",
        _ => return None,
    };

    let middle = &clean[1..8];
    let letter_part = clean.chars().nth(8)?.to_ascii_uppercase();

    let full_number_str = format!("{}{}", prefix_val, middle);
    let num: u64 = full_number_str.parse().ok()?;

    const DNI_LETTERS: &[u8] = b"TRWAGMYFPDXBNJZSQVHLCKE";
    let expected = DNI_LETTERS[(num % 23) as usize] as char;

    if letter_part == expected {
        Some(format!("{}{}{}", first, middle, expected))
    } else {
        None
    }
}

/// Brazil CPF: 11 digits with dual Modulo 11 check digits.
pub fn validate_br_cpf(raw: &str) -> Option<String> {
    let clean: String = raw.chars().filter(|c| c.is_ascii_digit()).collect();
    if clean.len() != 11 {
        return None;
    }

    // Check for invalid identical digit sequences (e.g. 11111111111)
    let first = clean.chars().next()?;
    if clean.chars().all(|c| c == first) {
        return None;
    }

    let digits: Vec<u32> = clean.chars().map(|c| c.to_digit(10).unwrap()).collect();

    // Verify first check digit
    let weights_1: [u32; 9] = [10, 9, 8, 7, 6, 5, 4, 3, 2];
    let d1 = compute_mod11(&digits[..9], &weights_1);
    if d1 != digits[9] {
        return None;
    }

    // Verify second check digit
    let weights_2: [u32; 10] = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2];
    let d2 = compute_mod11(&digits[..10], &weights_2);
    if d2 != digits[10] {
        return None;
    }

    Some(clean)
}

/// USA SSN: 9 digits. Area != 000, 666, 900..999. Group != 00. Serial != 0000.
pub fn validate_us_ssn(raw: &str) -> Option<String> {
    let clean: String = raw.chars().filter(|c| c.is_ascii_digit()).collect();
    if clean.len() != 9 {
        return None;
    }

    let area: u32 = clean[..3].parse().ok()?;
    let group: u32 = clean[3..5].parse().ok()?;
    let serial: u32 = clean[5..9].parse().ok()?;

    if area == 0 || area == 666 || area >= 900 {
        return None;
    }
    if group == 0 || serial == 0 {
        return None;
    }

    Some(format!("{}-{}-{}", &clean[..3], &clean[3..5], &clean[5..9]))
}

/// France NIF (Numéro d'Immatriculation Fiscale): 13 digits with Modulo 97 check.
pub fn validate_fr_nif(raw: &str) -> Option<String> {
    let clean: String = raw.chars().filter(|c| c.is_ascii_digit()).collect();
    if clean.len() != 13 {
        return None;
    }

    let base: u64 = clean[..11].parse().ok()?;
    let check: u64 = clean[11..13].parse().ok()?;

    let expected = base % 97;
    if check == expected {
        Some(clean)
    } else {
        None
    }
}

/// Italy Codice Fiscale: 16 alphanumeric characters.
pub fn validate_it_codice_fiscale(raw: &str) -> Option<String> {
    let clean: String = raw
        .chars()
        .filter(|c| c.is_alphanumeric())
        .map(|c| c.to_ascii_uppercase())
        .collect();
    if clean.len() != 16 {
        return None;
    }

    const ODD_TABLE: [u32; 36] = [
        1, 0, 5, 7, 9, 13, 15, 17, 19, 21, // 0-9
        1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24,
        23, // A-Z
    ];

    let mut sum: u32 = 0;
    for (i, ch) in clean[..15].chars().enumerate() {
        let val = match ch {
            '0'..='9' => (ch as u32) - ('0' as u32),
            'A'..='Z' => (ch as u32) - ('A' as u32) + 10,
            _ => return None,
        };

        if i % 2 == 0 {
            // Odd position (1-indexed)
            sum += ODD_TABLE[val as usize];
        } else {
            // Even position (1-indexed)
            sum += if ch.is_ascii_digit() { val } else { val - 10 };
        }
    }

    let expected_char = ((sum % 26) as u8 + b'A') as char;
    let actual_char = clean.chars().nth(15)?;

    if actual_char == expected_char {
        Some(clean)
    } else {
        None
    }
}

/// Mexico CURP: 18 alphanumeric characters.
pub fn validate_mx_curp(raw: &str) -> Option<String> {
    let clean: String = raw
        .chars()
        .filter(|c| c.is_alphanumeric())
        .map(|c| c.to_ascii_uppercase())
        .collect();
    if clean.len() != 18 {
        return None;
    }

    // Check basic structure: 4 letters + 6 digits + 1 gender + 2 state + 3 consonants + 2 check
    let letters_start = clean[..4].chars().all(|c| c.is_ascii_alphabetic());
    let date_part = clean[4..10].chars().all(|c| c.is_ascii_digit());
    let gender = clean.chars().nth(10)?;
    if !letters_start || !date_part || (gender != 'H' && gender != 'M' && gender != 'X') {
        return None;
    }

    Some(clean)
}
