#!/usr/bin/env bash

################################################################################
# This script is for linting the code of DuoLogSync by using the Pylint tool   #
################################################################################

# Directory containing source code for DuoLogSync
SOURCE_DIR="duologsync"

# Directory containing the python file for correctly formatting Pylint output 
# for use with Gitlab
REPORT_FORMATTER_DIR="_ci/lib"

# Path to the file where the report created by Pylint should be saved
CODE_REPORT_PATH="${SOURCE_DIR}"/codequality.json

# Usage of bash substring expansion (${parameter:-word}) such that if 
# 'parameter' (CI_PROJECT_DIR) does not have a value, 'word' will be used. 
# In this case, 'word' is a git command which returns the root / top-level 
# directory for the current git repository
CI_PROJECT_DIR="${CI_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"

# Path to the custom report formatter script
export PYTHONPATH="${CI_PROJECT_DIR}"/"${REPORT_FORMATTER_DIR}"

# The f flag indicates to Pylint that a report should be produced, compatible 
# with Gitlab Code Climate. The report will be saved to the file indicated on 
# the last line. Pylint will lint all code in the directory passed and all 
# the subdirectories.
pylint -f pylint_to_gitlab_codeclimate.GitlabCodeClimateReporter \
    "${CI_PROJECT_DIR}"/"${SOURCE_DIR}" > \
    "${CI_PROJECT_DIR}"/"${CODE_REPORT_PATH}"
