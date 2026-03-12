-- Test data for clubs and players
-- This file contains sample data for testing the players module

-- Insert clubs (if they don't exist)
INSERT OR IGNORE INTO clubs (name) VALUES ('Барселона');
INSERT OR IGNORE INTO clubs (name) VALUES ('Реал Мадрид');
INSERT OR IGNORE INTO clubs (name) VALUES ('Манчестър Юнайтед');
INSERT OR IGNORE INTO clubs (name) VALUES ('Баерн Мюнхен');
INSERT OR IGNORE INTO clubs (name) VALUES ('ПСЖ');

-- Get club IDs for player inserts
-- Note: In actual tests, you should query these IDs dynamically

-- Insert players for Барселона
INSERT OR IGNORE INTO players (full_name, birth_date, nationality, position, number, club_id, status) VALUES
('Луис Масакре', '1992-10-20', 'Аржентина', 'FW', 10,
 (SELECT id FROM clubs WHERE name = 'Барселона'), 'active'),
('Марк-Андре тер Штеген', '1992-04-30', 'Германия', 'GK', 1,
 (SELECT id FROM clubs WHERE name = 'Барселона'), 'active'),
('Жерар Пике', '1987-02-02', 'Испания', 'DF', 3,
 (SELECT id FROM clubs WHERE name = 'Барселона'), 'active'),
('Серхио Бускетс', '1988-07-16', 'Испания', 'MF', 5,
 (SELECT id FROM clubs WHERE name = 'Барселона'), 'active'),
('Анис Фати', '2001-10-31', 'Мароко', 'FW', 22,
 (SELECT id FROM clubs WHERE name = 'Барселона'), 'active');

-- Insert players for Реал Мадрид
INSERT OR IGNORE INTO players (full_name, birth_date, nationality, position, number, club_id, status) VALUES
('Карим Бензема', '1987-12-19', 'Франция', 'FW', 9,
 (SELECT id FROM clubs WHERE name = 'Реал Мадрид'), 'active'),
('Тони Кроос', '1990-01-04', 'Германия', 'MF', 8,
 (SELECT id FROM clubs WHERE name = 'Реал Мадрид'), 'active'),
('Серхио Рамос', '1986-03-30', 'Испания', 'DF', 4,
 (SELECT id FROM clubs WHERE name = 'Реал Мадрид'), 'active'),
('Кейлор Навас', '1986-12-15', 'Коста Рика', 'GK', 1,
 (SELECT id FROM clubs WHERE name = 'Реал Мадрид'), 'active'),
('Лука Модрич', '1985-09-09', 'Хърватия', 'MF', 10,
 (SELECT id FROM clubs WHERE name = 'Реал Мадрид'), 'active');

-- Insert players for Манчестър Юнайтед
INSERT OR IGNORE INTO players (full_name, birth_date, nationality, position, number, club_id, status) VALUES
('Кристиано Роналдо', '1985-02-05', 'Португалия', 'FW', 7,
 (SELECT id FROM clubs WHERE name = 'Манчестър Юнайтед'), 'active'),
('Бруно Фернандеш', '1994-09-08', 'Португалия', 'MF', 18,
 (SELECT id FROM clubs WHERE name = 'Манчестър Юнайтед'), 'active'),
('Маркус Рашфорд', '1997-10-31', 'Англия', 'FW', 10,
 (SELECT id FROM clubs WHERE name = 'Манчестър Юнайтед'), 'active'),
('Дейвид Де Хеа', '1990-11-07', 'Испания', 'GK', 1,
 (SELECT id FROM clubs WHERE name = 'Манчестър Юнайтед'), 'active'),
('Хари Магуайър', '1993-03-05', 'Англия', 'DF', 5,
 (SELECT id FROM clubs WHERE name = 'Манчестър Юнайтед'), 'active');

-- Additional players for variety
INSERT OR IGNORE INTO players (full_name, birth_date, nationality, position, number, club_id, status) VALUES
('Неймар', '1992-02-05', 'Бразилия', 'FW', 10,
 (SELECT id FROM clubs WHERE name = 'ПСЖ'), 'active'),
('Килиан Мбапе', '1998-12-20', 'Франция', 'FW', 7,
 (SELECT id FROM clubs WHERE name = 'ПСЖ'), 'active'),
('Роберто Левандовски', '1988-08-21', 'Полша', 'FW', 9,
 (SELECT id FROM clubs WHERE name = 'Баерн Мюнхен'), 'active'),
('Мануел Нойер', '1986-03-27', 'Германия', 'GK', 1,
 (SELECT id FROM clubs WHERE name = 'Баерн Мюнхен'), 'active');
