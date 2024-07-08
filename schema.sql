CREATE TABLE IF NOT EXISTS user_timezones (
    user_id BIGINT PRIMARY KEY,
    timezone TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bot_whitelist (
    user_id BIGINT PRIMARY KEY
);