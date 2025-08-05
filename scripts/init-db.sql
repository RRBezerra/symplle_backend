-- =============================================================================
-- INIT-DB.SQL - scripts/init-db.sql
-- Inicialização do banco PostgreSQL
-- =============================================================================

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Criar schema para chat system
CREATE SCHEMA IF NOT EXISTS chat;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Criar usuário para aplicação (se não existir)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'symplle_app') THEN
      CREATE ROLE symplle_app LOGIN PASSWORD 'symplle_app_password';
   END IF;
END
$$;

-- Dar permissões
GRANT USAGE ON SCHEMA public TO symplle_app;
GRANT USAGE ON SCHEMA chat TO symplle_app;
GRANT USAGE ON SCHEMA analytics TO symplle_app;

GRANT CREATE ON SCHEMA public TO symplle_app;
GRANT CREATE ON SCHEMA chat TO symplle_app;
GRANT CREATE ON SCHEMA analytics TO symplle_app;

-- =============================================================================
-- TABELAS BASE (Migradas do SQLite)
-- =============================================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email CITEXT UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    profile_image VARCHAR(255),
    password_hash VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE,
    premium_expires_at TIMESTAMP,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Countries table
CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) NOT NULL UNIQUE,
    phone_code VARCHAR(10) NOT NULL,
    flag_emoji VARCHAR(10),
    currency VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Phone OTPs table
CREATE TABLE IF NOT EXISTS phone_otps (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '10 minutes'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Posts table (mantendo compatibilidade)
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT,
    privacy VARCHAR(20) DEFAULT 'public',
    post_type VARCHAR(20) DEFAULT 'text',
    media_urls JSONB,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Likes table
CREATE TABLE IF NOT EXISTS likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, post_id)
);

-- Comments table
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    parent_comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    likes_count INTEGER DEFAULT 0,
    replies_count INTEGER DEFAULT 0,
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CHAT SYSTEM TABLES
-- =============================================================================

-- Chat rooms/conversations
CREATE TABLE IF NOT EXISTS chat.rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    description TEXT,
    room_type VARCHAR(20) NOT NULL DEFAULT 'direct', -- 'direct', 'group', 'channel'
    is_private BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL REFERENCES users(id),
    max_members INTEGER DEFAULT 100,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat room members
CREATE TABLE IF NOT EXISTS chat.room_members (
    id SERIAL PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES chat.rooms(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- 'admin', 'moderator', 'member'
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_read_at TIMESTAMP,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    is_muted BOOLEAN DEFAULT FALSE,
    UNIQUE(room_id, user_id)
);

-- Chat messages
CREATE TABLE IF NOT EXISTS chat.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES chat.rooms(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT,
    message_type VARCHAR(20) DEFAULT 'text', -- 'text', 'image', 'video', 'file', 'audio'
    media_url VARCHAR(500),
    media_metadata JSONB, -- file size, dimensions, etc.
    reply_to_message_id UUID REFERENCES chat.messages(id),
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    reactions JSONB DEFAULT '{}', -- emoji reactions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Message status (delivery, read receipts)
CREATE TABLE IF NOT EXISTS chat.message_status (
    id SERIAL PRIMARY KEY,
    message_id UUID NOT NULL REFERENCES chat.messages(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL, -- 'sent', 'delivered', 'read'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id, user_id)
);

-- =============================================================================
-- INDEXES PARA PERFORMANCE
-- =============================================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Posts indexes
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_privacy ON posts(privacy);
CREATE INDEX IF NOT EXISTS idx_posts_is_deleted ON posts(is_deleted);

-- Chat indexes
CREATE INDEX IF NOT EXISTS idx_chat_rooms_created_by ON chat.rooms(created_by);
CREATE INDEX IF NOT EXISTS idx_chat_rooms_type ON chat.rooms(room_type);
CREATE INDEX IF NOT EXISTS idx_chat_room_members_user_id ON chat.room_members(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_room_members_room_id ON chat.room_members(room_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_room_id ON chat.messages(room_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_sender_id ON chat.messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat.messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_message_status_message_id ON chat.message_status(message_id);

-- =============================================================================
-- FUNCTIONS & TRIGGERS
-- =============================================================================

-- Function para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON posts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_comments_updated_at BEFORE UPDATE ON comments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chat_rooms_updated_at BEFORE UPDATE ON chat.rooms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chat_messages_updated_at BEFORE UPDATE ON chat.messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- DADOS INICIAIS
-- =============================================================================

-- Inserir países básicos
INSERT INTO countries (name, code, phone_code, flag_emoji, currency) VALUES
('Brasil', 'BR', '+55', '🇧🇷', 'BRL'),
('United States', 'US', '+1', '🇺🇸', 'USD'),
('España', 'ES', '+34', '🇪🇸', 'EUR'),
('United Kingdom', 'GB', '+44', '🇬🇧', 'GBP'),
('France', 'FR', '+33', '🇫🇷', 'EUR'),
('Germany', 'DE', '+49', '🇩🇪', 'EUR'),
('Canada', 'CA', '+1', '🇨🇦', 'CAD'),
('Australia', 'AU', '+61', '🇦🇺', 'AUD'),
('Japan', 'JP', '+81', '🇯🇵', 'JPY'),
('India', 'IN', '+91', '🇮🇳', 'INR')
ON CONFLICT (code) DO NOTHING;

-- Usuário admin de desenvolvimento
INSERT INTO users (username, email, first_name, last_name, email_verified, phone_verified, is_active) VALUES
('admin', 'admin@symplle.com', 'Admin', 'Symplle', TRUE, TRUE, TRUE),
('test_user', 'test@symplle.com', 'Test', 'User', TRUE, TRUE, TRUE)
ON CONFLICT (email) DO NOTHING;

-- =============================================================================
-- ANALYTICS SCHEMA (Para métricas)
-- =============================================================================

CREATE TABLE IF NOT EXISTS analytics.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics.events(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics.events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics.events(created_at DESC);

-- =============================================================================
-- COMENTÁRIOS FINAIS
-- =============================================================================
COMMENT ON DATABASE symplle_dev IS 'Symplle Enterprise - Development Database';
COMMENT ON SCHEMA chat IS 'Chat system tables and functions';
COMMENT ON SCHEMA analytics IS 'Analytics and tracking tables';