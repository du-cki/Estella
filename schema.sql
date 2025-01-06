CREATE TABLE IF NOT EXISTS user_timezones (
    user_id BIGINT PRIMARY KEY,
    timezone TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bot_blacklist (
    user_id BIGINT PRIMARY KEY,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS minecraft_heads (
    uuid TEXT PRIMARY KEY,
    emoji_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)