-- Seed data for Football Manager
-- 8 Bulgarian clubs, multiple players per club, 2 leagues

-- ============================================
-- CLUBS (8 Bulgarian clubs)
-- ============================================
INSERT OR IGNORE INTO clubs (name) VALUES
('Левски София'),
('ЦСКА София'),
('Лудогорец Разград'),
('Ботев Пловдив'),
('Славия София'),
('Берое Стара Загора'),
('Черно море Варна'),
('Локомотив Пловдив');

-- ============================================
-- PLAYERS (3-4 players per club)
-- ============================================

-- Левски София players
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Пламен Илиев', '1991-11-30', 'България', 'GK', 1, 'active', id FROM clubs WHERE name = 'Левски София';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Андrian Краев', '1997-02-01', 'България', 'DF', 5, 'active', id FROM clubs WHERE name = 'Левски София';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Ивайло Чочев', '1993-07-18', 'България', 'MF', 8, 'active', id FROM clubs WHERE name = 'Левски София';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Роналдо', '1985-02-05', 'Португалия', 'FW', 7, 'active', id FROM clubs WHERE name = 'Левски София';

-- ЦСКА София players
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Густаво Бусато', '1990-10-23', 'Бразилия', 'GK', 25, 'active', id FROM clubs WHERE name = 'ЦСКА София';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Журо Катич', '1993-05-05', 'Босна и Херцеговина', 'DF', 4, 'active', id FROM clubs WHERE name = 'ЦСКА София';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Гraham Кери', '1993-05-20', 'Ирландия', 'MF', 10, 'active', id FROM clubs WHERE name = 'ЦСКА София';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Мауридес', '1994-03-10', 'Бразилия', 'FW', 9, 'active', id FROM clubs WHERE name = 'ЦСКА София';

-- Лудогорец Разград players
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Серджио Падт', '1990-06-06', 'Холандия', 'GK', 1, 'active', id FROM clubs WHERE name = 'Лудогорец Разград';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Антон Недялков', '1993-04-30', 'България', 'DF', 3, 'active', id FROM clubs WHERE name = 'Лудогорец Разград';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Клаудиу Кешеру', '1986-12-02', 'Румъния', 'MF', 28, 'active', id FROM clubs WHERE name = 'Лудогорец Разград';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Бернард Текпетей', '1997-09-03', 'Гана', 'FW', 11, 'active', id FROM clubs WHERE name = 'Лудогорец Разград';

-- Ботев Пловдив players
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Христо Иванов', '1982-02-06', 'България', 'GK', 33, 'active', id FROM clubs WHERE name = 'Ботев Пловдив';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Филип Филипов', '1988-08-02', 'България', 'DF', 6, 'active', id FROM clubs WHERE name = 'Ботев Пловдив';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Тодор Неделев', '1993-02-07', 'България', 'MF', 17, 'active', id FROM clubs WHERE name = 'Ботев Пловдив';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Атанас Илиев', '1994-10-09', 'България', 'FW', 19, 'active', id FROM clubs WHERE name = 'Ботев Пловдив';

-- Славия София players
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Светослав Вуцов', '2002-07-09', 'България', 'GK', 1, 'active', id FROM clubs WHERE name = 'Славия София';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Андреа Христов', '1999-03-01', 'България', 'DF', 15, 'active', id FROM clubs WHERE name = 'Славия София';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Ертан Томбак', '1999-03-30', 'България', 'MF', 77, 'active', id FROM clubs WHERE name = 'Славия София';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Ивайло Димитров', '1989-03-26', 'България', 'FW', 9, 'active', id FROM clubs WHERE name = 'Славия София';

-- Берое Стара Загора players
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Генадий Ганев', '1992-01-24', 'България', 'GK', 12, 'active', id FROM clubs WHERE name = 'Берое Стара Загора';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Иван Минчев', '1991-05-16', 'България', 'DF', 2, 'active', id FROM clubs WHERE name = 'Берое Стара Загора';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Бригидо Нгала', '1992-11-21', 'Камерун', 'MF', 8, 'active', id FROM clubs WHERE name = 'Берое Стара Загора';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Алиун Фал', '1989-11-30', 'Сенегал', 'FW', 10, 'active', id FROM clubs WHERE name = 'Берое Стара Загора';

-- Черно море Варна players
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Иван Дюлгеров', '1999-07-15', 'България', 'GK', 1, 'active', id FROM clubs WHERE name = 'Черно море Варна';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Виктор Попов', '2000-03-05', 'България', 'DF', 22, 'active', id FROM clubs WHERE name = 'Черно море Варна';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Пабло Гарсия', '1999-06-23', 'Уругвай', 'MF', 6, 'active', id FROM clubs WHERE name = 'Черно море Варна';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Жоржиньо', '1995-10-26', 'Бразилия', 'FW', 11, 'active', id FROM clubs WHERE name = 'Черно море Варна';

-- Локомотив Пловдив players
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Илко Пиргов', '1986-05-23', 'България', 'GK', 1, 'active', id FROM clubs WHERE name = 'Локомотив Пловдив';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Динис Алмейда', '1991-10-05', 'Португалия', 'DF', 4, 'active', id FROM clubs WHERE name = 'Локомотив Пловдив';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Петър Витанов', '1995-03-10', 'България', 'MF', 18, 'active', id FROM clubs WHERE name = 'Локомотив Пловдив';
INSERT INTO players (full_name, birth_date, nationality, position, number, status, club_id)
SELECT 'Димитър Илиев', '1988-09-25', 'България', 'FW', 10, 'active', id FROM clubs WHERE name = 'Локомотив Пловдив';

-- ============================================
-- LEAGUES (2 leagues)
-- ============================================
INSERT INTO leagues (name, season) VALUES
('Първа Лига', '2024/2025'),
('Купа на България', '2024/2025');

-- ============================================
-- LEAGUE TEAMS - First League (all 8 clubs)
-- ============================================
INSERT INTO league_teams (league_id, club_id)
SELECT l.id, c.id 
FROM leagues l, clubs c 
WHERE l.name = 'Първа Лига' AND l.season = '2024/2025' AND c.name IN 
('Левски София', 'ЦСКА София', 'Лудогорец Разград', 'Ботев Пловдив', 
 'Славия София', 'Берое Стара Загора', 'Черно море Варна', 'Локомотив Пловдив');

-- ============================================
-- LEAGUE TEAMS - Cup (first 4 clubs)
-- ============================================
INSERT INTO league_teams (league_id, club_id)
SELECT l.id, c.id 
FROM leagues l, clubs c 
WHERE l.name = 'Купа на България' AND l.season = '2024/2025' AND c.name IN 
('Левски София', 'ЦСКА София', 'Лудогорец Разград', 'Ботев Пловдив');

-- ============================================
-- SAMPLE TRANSFERS
-- ============================================

-- Transfer from Botev to CSKA (example historical transfer)
INSERT INTO transfers (player_id, from_club_id, to_club_id, transfer_date, fee, note)
SELECT p.id, c1.id, c2.id, '2024-06-15', 500000, 'Трансфер от Ботев към ЦСКА'
FROM players p, clubs c1, clubs c2
WHERE p.full_name = 'Тодор Неделев' AND c1.name = 'Ботев Пловдив' AND c2.name = 'ЦСКА София';

-- Update player club after transfer
UPDATE players SET club_id = (SELECT id FROM clubs WHERE name = 'ЦСКА София')
WHERE full_name = 'Тодор Неделев';

-- Transfer from free agent to Levski
INSERT INTO transfers (player_id, from_club_id, to_club_id, transfer_date, fee, note)
SELECT p.id, NULL, c.id, '2024-07-01', NULL, 'Свободен трансфер'
FROM players p, clubs c
WHERE p.full_name = 'Роналдо' AND c.name = 'Левски София';

-- Transfer from Slavia to Ludogorets
INSERT INTO transfers (player_id, from_club_id, to_club_id, transfer_date, fee, note)
SELECT p.id, c1.id, c2.id, '2024-08-20', 300000, 'Трансфер от Славия към Лудогорец'
FROM players p, clubs c1, clubs c2
WHERE p.full_name = 'Андреа Христов' AND c1.name = 'Славия София' AND c2.name = 'Лудогорец Разград';

-- Update player club after transfer
UPDATE players SET club_id = (SELECT id FROM clubs WHERE name = 'Лудогорец Разград')
WHERE full_name = 'Андреа Христов';
