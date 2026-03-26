import os
import logging
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import db as database_db
from chatbot.router import bot
from services import clubs_service
import utils.logger as logger

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE = os.path.join(BASE_DIR, "commands.log")
SCHEMA_FILE = os.path.join(BASE_DIR, "sql", "schema.sql")

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler(sys.stdout)]
    )

def init_db():
    conn = database_db.get_connection()
    try:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            script = f.read()
        conn.executescript(script)
        conn.commit()
    except FileNotFoundError:
        raise RuntimeError("Schema file not found. Ensure sql/schema.sql exists.")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize database schema: {e}")

def main_loop():
    setup_logging()
    init_db()
    logging.info("Chatbot started.")
    print("Chatbot started. (помощ за команди)")

    while True:
        try:
            user_input = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            logging.info("INPUT: <signal> | OUTPUT: Exiting.")
            break

        if not user_input:
            continue

        response, exit_flag = bot.handle(user_input)
        print(response)

        logging.info(f"INPUT: {user_input} | OUTPUT: {response}")

        if exit_flag:
            break

if __name__ == "__main__":
    main_loop()
