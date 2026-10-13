-- Migration 005: Add Configurable Capitalisation Threshold to Practices
-- HMRC Capital Allowances Act 2001 (CAA 2001) / BIM35000 De Minimis Practice Rule

ALTER TABLE practices 
ADD COLUMN IF NOT EXISTS capitalisation_threshold_gbp NUMERIC(10, 2) DEFAULT 500.00;
