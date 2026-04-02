CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    birth_date TEXT NOT NULL,
    nationality TEXT NOT NULL,
    position TEXT NOT NULL CHECK(position IN ('GK', 'DF', 'MF', 'FW')),
    number INTEGER NOT NULL CHECK(number >= 1 AND number <= 99),
    status TEXT NOT NULL DEFAULT 'active',
    club_id INTEGER,
    FOREIGN KEY (club_id) REFERENCES clubs(id)
);

CREATE INDEX IF NOT EXISTS idx_players_club_id ON players(club_id);

CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    from_club_id INTEGER,
    to_club_id INTEGER NOT NULL,
    transfer_date TEXT NOT NULL,
    fee INTEGER,
    note TEXT,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (from_club_id) REFERENCES clubs(id),
    FOREIGN KEY (to_club_id) REFERENCES clubs(id),
    CHECK (to_club_id != from_club_id)
);

CREATE INDEX IF NOT EXISTS idx_transfers_player_id ON transfers(player_id);
CREATE INDEX IF NOT EXISTS idx_transfers_from_club_id ON transfers(from_club_id);
CREATE INDEX IF NOT EXISTS idx_transfers_to_club_id ON transfers(to_club_id);
CREATE INDEX IF NOT EXISTS idx_transfers_date ON transfers(transfer_date);

CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    season TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, season)
);

CREATE TABLE IF NOT EXISTS league_teams (
    league_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (league_id, club_id),
    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
    FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_league_teams_league_id ON league_teams(league_id);
CREATE INDEX IF NOT EXISTS idx_league_teams_club_id ON league_teams(club_id);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL,
    round_no INTEGER NOT NULL,
    home_club_id INTEGER NOT NULL,
    away_club_id INTEGER NOT NULL,
    match_date TEXT,
    home_goals INTEGER,
    away_goals INTEGER,
    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
    FOREIGN KEY (home_club_id) REFERENCES clubs(id),
    FOREIGN KEY (away_club_id) REFERENCES clubs(id),
    CHECK (home_club_id != away_club_id)
);

CREATE INDEX IF NOT EXISTS idx_matches_league_id ON matches(league_id);
CREATE INDEX IF NOT EXISTS idx_matches_round_no ON matches(round_no);
CREATE INDEX IF NOT EXISTS idx_matches_home_club_id ON matches(home_club_id);
CREATE INDEX IF NOT EXISTS idx_matches_away_club_id ON matches(away_club_id);