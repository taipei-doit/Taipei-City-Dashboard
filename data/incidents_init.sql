-- ============================================
-- Taipei City Dashboard - Incidents Table
-- Complete Schema Initialization
-- Created: 2026-05-02
-- ============================================

-- Drop existing table if needed (for fresh start)
-- Uncomment the line below only if you want to completely reset the table
-- DROP TABLE IF EXISTS incidents CASCADE;

-- Create incidents table from scratch
CREATE TABLE IF NOT EXISTS incidents (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    type VARCHAR(255) NOT NULL,
    description TEXT,
    distance DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    place TEXT DEFAULT '',
    "time" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for optimized queries
CREATE INDEX IF NOT EXISTS idx_incidents_place ON incidents(place);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(type);
CREATE INDEX IF NOT EXISTS idx_incidents_status_type ON incidents(status, type);
CREATE INDEX IF NOT EXISTS idx_incidents_time ON incidents("time");
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);
CREATE INDEX IF NOT EXISTS idx_incidents_deleted_at ON incidents(deleted_at);

-- Grant permissions (adjust user names as needed)
-- Uncomment and modify if using a specific database user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON incidents TO dashboard_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO dashboard_user;

-- ============================================
-- Sample Data (Optional - for testing)
-- ============================================

-- Insert sample incidents (uncomment if needed for testing)
-- INSERT INTO incidents (type, description, distance, latitude, longitude, place, status)
-- VALUES 
--     ('食安', '發現過期食材', 150.5, 25.0330, 121.5654, '玉坊小吃店\n新北市中和區興南路1段75號', 'open'),
--     ('衛生', '環境髒亂', 280.3, 25.0450, 121.5500, '老張咖啡\n台北市信義區松高路1號', 'investigating');

-- ============================================
-- Verification Queries
-- ============================================

-- Check if table was created successfully
-- SELECT * FROM information_schema.tables WHERE table_name='incidents';

-- Check columns
-- SELECT column_name, data_type, is_nullable, column_default 
-- FROM information_schema.columns 
-- WHERE table_name='incidents'
-- ORDER BY ordinal_position;

-- Check indexes
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename='incidents';
