-- Cerina Foundry Database Schema
-- Creates tables for checkpointing and state management

-- Create database (run this manually if needed)
-- CREATE DATABASE cerina_foundry;

-- Connect to cerina_foundry database
\c cerina_foundry;

-- =====================================================
-- LangGraph Checkpointing Tables
-- =====================================================

-- Main checkpoint table for state persistence
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id VARCHAR(255) NOT NULL,
    checkpoint_id VARCHAR(255) NOT NULL,
    parent_checkpoint_id VARCHAR(255),
    checkpoint JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at);

-- =====================================================
-- Application-specific Tables
-- =====================================================

-- Workflow execution logs
CREATE TABLE IF NOT EXISTS workflow_logs (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workflow_logs_thread_id ON workflow_logs(thread_id);

-- Protocol drafts (for historical tracking)
CREATE TABLE IF NOT EXISTS protocol_drafts (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    safety_score FLOAT,
    empathy_score FLOAT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(thread_id, version)
);

CREATE INDEX IF NOT EXISTS idx_protocol_drafts_thread_id ON protocol_drafts(thread_id);

-- Safety flags tracking
CREATE TABLE IF NOT EXISTS safety_flags (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    draft_version INTEGER NOT NULL,
    segment TEXT NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    suggestion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_safety_flags_thread_id ON safety_flags(thread_id);

-- Human review sessions
CREATE TABLE IF NOT EXISTS human_reviews (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    draft_version INTEGER NOT NULL,
    reviewer_notes TEXT,
    approved BOOLEAN,
    edited_content TEXT,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_human_reviews_thread_id ON human_reviews(thread_id);

-- =====================================================
-- Views for Analytics
-- =====================================================

-- View for latest state per thread
CREATE OR REPLACE VIEW latest_checkpoints AS
SELECT DISTINCT ON (thread_id)
    thread_id,
    checkpoint_id,
    checkpoint,
    metadata,
    created_at
FROM checkpoints
ORDER BY thread_id, created_at DESC;

-- View for safety analytics
CREATE OR REPLACE VIEW safety_analytics AS
SELECT 
    sf.thread_id,
    sf.risk_level,
    COUNT(*) as flag_count,
    AVG(pd.safety_score) as avg_safety_score
FROM safety_flags sf
JOIN protocol_drafts pd ON sf.thread_id = pd.thread_id AND sf.draft_version = pd.version
GROUP BY sf.thread_id, sf.risk_level;

COMMENT ON DATABASE cerina_foundry IS 'Cerina Protocol Foundry - Multi-agent CBT protocol generation system';
