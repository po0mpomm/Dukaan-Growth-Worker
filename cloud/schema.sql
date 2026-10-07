-- =============================================================================
-- Dukaan Growth Worker — Cloud Plane PostgreSQL Schema
-- TRD §7.2, ADR 008
-- k-Anonymity Threshold: k >= 5 (suppresses any cohort with fewer than 5 shops)
-- =============================================================================

CREATE TABLE IF NOT EXISTS shop_aggregates (
    id SERIAL PRIMARY KEY,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    shop_pid VARCHAR(64) NOT NULL,
    month VARCHAR(7) NOT NULL,
    region_type VARCHAR(20) NOT NULL,
    sales_change_band VARCHAR(20) NOT NULL,
    credit_share_band VARCHAR(20) NOT NULL,
    overdue_band VARCHAR(20) NOT NULL,
    completeness_band VARCHAR(20) NOT NULL,
    action_completion_band VARCHAR(20) NOT NULL,
    rules_fired JSONB NOT NULL,
    CONSTRAINT unique_shop_month UNIQUE (shop_pid, month)
);

-- Index for macro-cohort aggregations
CREATE INDEX IF NOT EXISTS idx_aggregates_cohort ON shop_aggregates (month, region_type, sales_change_band);

-- Macro-Cohort Summary View with k >= 5 Suppression (ADR 008)
-- Any cohort cell with count < 5 is masked/suppressed to prevent deanonymization.
CREATE OR REPLACE VIEW mc_summary_k_suppressed AS
SELECT
    month,
    region_type,
    sales_change_band,
    CASE 
        WHEN COUNT(*) >= 5 THEN COUNT(*)
        ELSE NULL -- Suppressed for privacy
    END AS shop_count,
    CASE 
        WHEN COUNT(*) >= 5 THEN 'UNMASKED'
        ELSE 'SUPPRESSED_K_LT_5'
    END AS suppression_status
FROM shop_aggregates
GROUP BY month, region_type, sales_change_band;
