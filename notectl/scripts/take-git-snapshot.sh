#!/bin/bash

# Check if there are changes to commit
if [[ -n $(git status -s) ]]; then
    # Run git add
    git add -A > /dev/null 2>&1

    # Create a timestamp for the commit message
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")

    # Run git commit with the timestamped message
    git commit -m "[snapshot] $timestamp" > /dev/null 2>&1

    # Print the created snapshot message
    echo "Created snapshot at: $timestamp"
else
    echo "No changes to snapshot."
fi
