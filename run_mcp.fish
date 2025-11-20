#!/usr/bin/env fish

# Get the project root directory
set project_root (dirname (status -f))
cd $project_root

# Activate venv
if test -d "venv"
    source venv/bin/activate.fish
end

# Load environment variables
if test -f .env
    for line in (cat .env | grep -v '^#' | string match -r '.')
        set parts (string split -m 1 "=" $line)
        if test (count $parts) -eq 2
            set -gx $parts[1] (string trim --chars='"' $parts[2])
        end
    end
end

# Run with PYTHONPATH set to project root
env PYTHONPATH=$project_root python -m src.mcp_server

