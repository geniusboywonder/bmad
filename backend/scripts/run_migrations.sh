#!/bin/bash

# This script runs the database migrations using Alembic.
# It loads the environment variables from the .env file before running the migrations.

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load the environment variables from the .env file
if [ -f "$DIR/../.env" ]; then
  export $(cat "$DIR/../.env" | sed 's/#.*//g' | xargs)
fi

# Run the alembic upgrade head command
alembic upgrade head
