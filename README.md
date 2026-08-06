# InfoStream

## Overview
InfoStream is an AI-powered platform that monitors Telegram channels, organizes information into meaningful categories, and helps users quickly find relevant updates. It was built to reduce information overload by making large volumes of Telegram content searchable and easy to understand.

## Why I Built It
Many organizations and individuals rely on Telegram for news and communication, but important information is often buried across dozens of channels. InfoStream automatically collects, organizes, and summarizes this information, allowing users to stay informed without reading every message.

## Key Features
- Monitors 100+ Telegram channels
- Organizes information by topic
- AI-generated summaries
- Natural language search
- Fast and intuitive web interface

## My Contributions
I designed and developed the platform, including the AI pipeline, data collection system, search functionality, backend services, and deployment.

## Technologies
- Python
- FastAPI
- PostgreSQL
- AI language models
- Docker

## Installation
python src/app/core/bot/bot.py
uvicorn app.main:app --reload
