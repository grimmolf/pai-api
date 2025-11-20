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
    for line in (cat .env | grep -v '^#' | string match -r '.')
        set parts (string split -m 1 "=" $line)
        if test (count $parts) -eq 2
            set -gx $parts[1] (string trim --chars='"' $parts[2])
        end
    end
end

echo "Starting Bob API Server on port $PAI_PORT..."
uvicorn src.main:app --reload --port $PAI_PORT --host 0.0.0.0
