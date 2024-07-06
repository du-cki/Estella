CREATE TABLE IF NOT EXISTS user_timezones (
    user_id BIGINT NOT NULL,
    timezone TEXT NOT NULL,

    PRIMARY KEY (user_id)
) 