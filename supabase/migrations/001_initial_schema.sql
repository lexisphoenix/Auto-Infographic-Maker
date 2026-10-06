-- Migration 001: Initial Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS infographic_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_fingerprint VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    key_facts JSONB,
    novelty_score NUMERIC(4, 2),
    viz_score NUMERIC(4, 2),
    priority_score NUMERIC(4, 2),
    design_brief JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    image_url TEXT,
    html_path TEXT,
    caption TEXT,
    hashtags JSONB,
    scheduled_for TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS topic_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    last_processed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS infographic_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    infographic_id UUID REFERENCES infographic_queue(id),
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    shares INT DEFAULT 0,
    impressions INT DEFAULT 0,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_infographic_status ON infographic_queue(status);
CREATE INDEX idx_infographic_priority ON infographic_queue(priority_score DESC);
CREATE INDEX idx_infographic_scheduled ON infographic_queue(scheduled_for);
CREATE INDEX idx_topic_fingerprint ON infographic_queue(topic_fingerprint);

-- Row Level Security (RLS)
ALTER TABLE infographic_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE infographic_analytics ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service Role Full Access Infographics" ON infographic_queue
    FOR ALL USING (true);
CREATE POLICY "Service Role Full Access Topics" ON topic_history
    FOR ALL USING (true);
CREATE POLICY "Service Role Full Access Analytics" ON infographic_analytics
    FOR ALL USING (true);
