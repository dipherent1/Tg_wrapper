# Tg_wrapper

python src/app/core/bot/bot.py
uvicorn app.main:app --reload

# 1. Connect and navigate to project

ssh -i ... user@host
cd /path/to/project

# 2. Update code and dependencies

git pull
source .venv/bin/activate
pip install -r requirements.txt

# 3. Update the database (if needed)

alembic upgrade head
