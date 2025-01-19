CREATE TABLE IF NOT EXISTS user_timezones (
    user_id BIGINT PRIMARY KEY,
    timezone TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bot_blacklist (
    user_id BIGINT PRIMARY KEY,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS minecraft_servers (
    assigned_to BIGINT PRIMARY KEY,
    parent_id BIGINT, -- only present in thread channels.
    assigned_by BIGINT NOT NULL,
    channel_type INT NOT NULL,
    minecraft_server_type INT NOT NULL,
    ip TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS minecraft_heads (
    uuid TEXT PRIMARY KEY,
    emoji_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
