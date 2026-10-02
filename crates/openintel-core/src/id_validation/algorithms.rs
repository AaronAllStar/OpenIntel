/// Luhn algorithm (Mod 10) checksum verification.
pub fn verify_luhn(digits: &str) -> bool {
    let mut sum = 0;
    let mut alternate = false;

    for ch in digits.chars().rev() {
        if let Some(digit) = ch.to_digit(10) {
            let mut val = digit;
            if alternate {
                val *= 2;
                if val > 9 {
                    val -= 9;
                }
            }
            sum += val;
            alternate = !alternate;
        } else {
            return false;
        }
    }

    sum % 10 == 0
}

/// Modulo 11 algorithm with weighted multiplier vector.
pub fn compute_mod11(digits: &[u32], weights: &[u32]) -> u32 {
    let sum: u32 = digits
        .iter()
        .zip(weights.iter())
        .map(|(&d, &w)| d * w)
        .sum();
    let rem = sum % 11;
    if rem < 2 {
        0
    } else {
        11 - rem
    }
}

/// Verhoeff checksum calculation using D5 dihedral group permutations.
const MULTIPLICATION_TABLE: [[u8; 10]; 10] = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
];

const PERMUTATION_TABLE: [[u8; 10]; 8] = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
];

pub fn verify_verhoeff(digits: &str) -> bool {
    let mut c = 0;
    for (i, ch) in digits.chars().rev().enumerate() {
        if let Some(digit) = ch.to_digit(10) {
            let p = PERMUTATION_TABLE[i % 8][digit as usize];
            c = MULTIPLICATION_TABLE[c as usize][p as usize];
        } else {
            return false;
        }
    }
    c == 0
}
