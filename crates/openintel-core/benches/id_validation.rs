use criterion::{black_box, criterion_group, criterion_main, Criterion};
use openintel_core::id_validation::{validate_batch, validate_single};

fn bench_single_validations(c: &mut Criterion) {
    let mut group = c.benchmark_group("national_id_single");

    group.bench_function("es_dni_valid", |b| {
        b.iter(|| validate_single(black_box("12345678Z")))
    });

    group.bench_function("br_cpf_valid", |b| {
        b.iter(|| validate_single(black_box("11144477735")))
    });

    group.bench_function("us_ssn_valid", |b| {
        b.iter(|| validate_single(black_box("123-45-6789")))
    });

    group.bench_function("unrecognized_id", |b| {
        b.iter(|| validate_single(black_box("NONEXISTENT_ID_99999")))
    });

    group.finish();
}

fn bench_batch_validations(c: &mut Criterion) {
    let mut group = c.benchmark_group("national_id_batch");

    let batch_1000: Vec<String> = (0..1000)
        .map(|i| {
            if i % 3 == 0 {
                "12345678Z".to_string()
            } else if i % 3 == 1 {
                "11144477735".to_string()
            } else {
                format!("INVALID_SAMPLE_{}", i)
            }
        })
        .collect();

    group.bench_function("batch_1000_rayon", |b| {
        b.iter(|| validate_batch(black_box(&batch_1000)))
    });

    group.finish();
}

criterion_group!(benches, bench_single_validations, bench_batch_validations);
criterion_main!(benches);
