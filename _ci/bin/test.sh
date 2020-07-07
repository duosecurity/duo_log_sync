#!/usr/bin/env bash

################################################################################
# This script is for running Unit Tests on DuoLogSync by using the Pytest tool #
################################################################################

# A number 1-255 indicates an error
ERROR=1

# The number 0 indicates success
SUCCESS=0
EXIT_STATUS=$ERROR

# Usage of bash substring expansion (${parameter:-word}) such that if 
# 'parameter' (CI_PROJECT_DIR) does not have a value, 'word' will be used. 
# In this case, 'word' is a git command which returns the root / top-level 
# directory for the current git repository
CI_PROJECT_DIR="${CI_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"

# Add directory to stack, allowing a person to run this test from anywhere 
# in the project strucutre and easily returning back to the original directory
pushd "${CI_PROJECT_DIR}" || exit $EXIT_STATUS

# Run pytest and check its return condition
if pytest; then
    echo "Unit Tests passed"
    EXIT_STATUS=$SUCCESS
else
    echo "Unit Tests failed"
fi

# Take CI_PROJECT_DIR off the directory stack, expose the original directory
popd || exit $EXIT_STATUS
exit $EXIT_STATUS
