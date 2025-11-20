#!/usr/bin/env fish
source venv/bin/activate.fish
uvicorn src.main:app --reload --port 8000

