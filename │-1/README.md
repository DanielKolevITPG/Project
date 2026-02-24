# Football Manager Project

This project is a Football Manager application that allows users to manage football clubs through a chatbot interface. The application supports basic CRUD operations for clubs and utilizes a SQLite database for data storage.

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd project
   ```
3. Install any required dependencies (if applicable).

## How to Run

To start the application, run the following command:
```
python src/main.py
```

## Example Commands

Here are some example commands you can use with the chatbot:

- Добави клуб Левски София (Add club Levski Sofia)
- Покажи всички клубове (Show all clubs)
- Изтрий клуб Ботев (Delete club Botev)
- помощ (help)
- изход (exit)

## Architecture

The application is structured in a modular way, separating concerns into different files:

- `main.py`: Contains the main loop of the application.
- `db.py`: Manages the database connection and SQL query execution.
- `chatbot.py`: Implements the chatbot architecture and intent detection.
- `clubs_service.py`: Provides CRUD operations for managing clubs.
- `schema.sql`: Defines the database schema for the clubs table.

This modular design ensures clean and maintainable code, allowing for easy updates and enhancements in the future.