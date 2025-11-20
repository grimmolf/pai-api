#!/usr/bin/env fish

# Check if venv exists
if not test -d "venv"
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate.fish
    pip install -r requirements.txt
end

source venv/bin/activate.fish

# Load .env variables if present for local overrides
if test -f .env
    export (cat .env | grep -v "^#" | xargs)
end

echo "Starting Bob API Server on port $PAI_PORT..."
uvicorn src.main:app --reload --port $PAI_PORT --host 0.0.0.0
