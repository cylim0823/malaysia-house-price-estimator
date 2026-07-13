# Real-Data Onboarding Guide

The demonstration generator and its metrics must never be used as evidence of Malaysian market accuracy. For a future approved dataset:

1. Confirm the licence permits training, derived models, reporting, predictions, retention, and publication.
2. Record source terms, version/date, attribution, access method, and redistribution limits.
3. Record price type and keep asking and completed-transaction datasets separate.
4. Map source columns to the canonical schema.
5. Import unchanged source payloads with batch, source, schema, and dataset versions.
6. Validate required fields and controlled values.
7. Clean reproducibly while preserving raw values and units.
8. Review rejected rows and structured reasons.
9. Review duplicate groups and canonical decisions.
10. Review outliers, parsing, units, and source consistency; preserve legitimate unusual properties.
11. Generate a quality report.
12. Check geographic, property-type, price-type, and date coverage.
13. Create time-ordered, duplicate-group-safe train, validation, and untouched test splits.
14. Train simple baselines before advanced models.
15. Select on validation data and use final test data once.
16. Define supported coverage using counts and segment errors.
17. Replace the synthetic bundle only after compatibility and coverage review.
18. Run the full suite without placing restricted records in the repository.
19. Update metrics, support matrices, limitations, disclaimers, and versions.
20. Deploy only after owner approval, data-rights review, security review, and credential setup.

Never place restricted raw data, personal information, credentials, or large model artifacts in the repository.

