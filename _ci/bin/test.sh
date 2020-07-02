#!/usr/bin/env bash

################################################################################
# This script is for running Unit Tests on DuoLogSync by using the Pytest tool #
################################################################################

# A number 1-255 indicates an error
ERROR=1

# The number 0 indicates success
SUCCESS=0
EXIT_STATUS=$ERROR

# Directory containing source code for DuoLogSync
SOURCE_DIRECTORY="duologsync"

# Directory containing Unit Tests for DuoLogSync
TESTS_DIRECTORY="tests"

# Usage of bash substring expansion (${parameter:-word}) such that if 
# 'parameter' (CI_PROJECT_DIR) does not have a value, 'word' will be used. 
# In this case, 'word' is a git command which returns the root / top-level 
# directory for the current git repository
CI_PROJECT_DIR="${CI_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"

# Move into the directory where Unit Tests are stored, or exit if the 
# directory doesn't exist
cd "${CI_PROJECT_DIR}"/"${TESTS_DIRECTORY}" || exit $EXIT_STATUS

# Not sure what this is used for, leave commented for now
# export PYTHONPATH="${CI_PROJECT_DIR}"/"${SOURCE_DIRECTORY}"

# Run pytest and check its return condition
if pytest; then
    echo "Unit Tests passed"
    EXIT_STATUS=$SUCCESS
else
    echo "Unit Tests failed"
fi

exit $EXIT_STATUS
