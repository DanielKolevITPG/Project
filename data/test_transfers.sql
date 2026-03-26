-- Phase 4 test data: clubs, players, and transfers

-- Insert clubs (Bulgarian clubs)
INSERT OR IGNORE INTO clubs (name) VALUES ('Левски');
INSERT OR IGNORE INTO clubs (name) VALUES ('Лудогорец');
INSERT OR IGNORE INTO clubs (name) VALUES ('ЦСКА');
INSERT OR IGNORE INTO clubs (name) VALUES ('Ботев Пловдив');

-- Insert players for Левски
INSERT OR IGNORE INTO players (full_name, birth_date, nationality, position, number, club_id, status) VALUES
('Иван Петров', '1995-03-15', 'България', 'MF', 10,
 (SELECT id FROM clubs WHERE name = 'Левски'), 'active'),
('Георги Йончев', '1998-07-22', 'България', 'FW', 9,
 (SELECT id FROM clubs WHERE name = 'Левски'), 'active'),
('Никола Тодоров', '1992-11-08', 'България', 'DF', 4,
 (SELECT id FROM clubs WHERE name = 'Левски'), 'active');

-- Insert players for Лудогорец
INSERT OR IGNORE INTO players (full_name, birth_date, nationality, position, number, club_id, status) VALUES
('Марин Орлинов', '1996-05-12', 'България', 'FW', 11,
 (SELECT id FROM clubs WHERE name = 'Лудогорец'), 'active'),
('Станислав Генчев', '1994-02-28', 'България', 'MF', 8,
 (SELECT id FROM clubs WHERE name = 'Лудогорец'), 'active'),
('Димитър Енев', '1990-08-15', 'България', 'DF', 5,
 (SELECT id FROM clubs WHERE name = 'Лудогорец'), 'active');

-- Insert transfers
-- Transfer 1: Иван Петров from Левски to Лудогорец
INSERT OR IGNORE INTO transfers (player_id, from_club_id, to_club_id, transfer_date, fee, note) VALUES
((SELECT id FROM players WHERE full_name = 'Иван Петров'),
 (SELECT id FROM clubs WHERE name = 'Левски'),
 (SELECT id FROM clubs WHERE name = 'Лудогорец'),
 '2025-06-15', 50000, 'Transfer to champions');

-- Transfer 2: Марин Орлинов from Левски to Лудогорец (earlier)
INSERT OR IGNORE INTO transfers (player_id, from_club_id, to_club_id, transfer_date, fee, note) VALUES
((SELECT id FROM players WHERE full_name = 'Марин Орлинов'),
 (SELECT id FROM clubs WHERE name = 'Левски'),
 (SELECT id FROM clubs WHERE name = 'Лудогорец'),
 '2024-01-10', 30000, NULL);

-- Transfer 3: Никола Тодоров from ЦСКА to Левски
INSERT OR IGNORE INTO transfers (player_id, from_club_id, to_club_id, transfer_date, fee, note) VALUES
((SELECT id FROM players WHERE full_name = 'Никола Тодоров'),
 (SELECT id FROM clubs WHERE name = 'ЦСКА'),
 (SELECT id FROM clubs WHERE name = 'Левски'),
 '2025-03-20', 25000, NULL);

-- Transfer 4: Георги Йончев from Ботев Пловдив to Левски
INSERT OR IGNORE INTO transfers (player_id, from_club_id, to_club_id, transfer_date, fee, note) VALUES
((SELECT id FROM players WHERE full_name = 'Георги Йончев'),
 (SELECT id FROM clubs WHERE name = 'Ботев Пловдив'),
 (SELECT id FROM clubs WHERE name = 'Левски'),
 '2025-01-05', 40000, 'Youth transfer');

-- Transfer 5: Димитър Е男性的 from ЦСКА to Лудогорец
INSERT OR IGNORE INTO transfers (player_id, from_club_id, to_club_id, transfer_date, fee, note) VALUES
((SELECT id FROM players WHERE full_name = 'Димитър Енев'),
 (SELECT id FROM clubs WHERE name = 'ЦСКА'),
 (SELECT id FROM clubs WHERE name = 'Лудогорец'),
 '2024-08-01', 60000, 'Defensive reinforcement');
