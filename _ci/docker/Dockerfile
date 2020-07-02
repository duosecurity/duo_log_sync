#syntax=docker/dockerfile:experimental
# Base our Docker image off of the Python 3.7 slim Docker image. Slim means 
# that only the minimal packages needed to run Python are included
FROM python:3.7-slim

# Mount is used for the run operation, rather than making a copy of DuoLogSync 
# onto the Docker container, because it is a more performant operation. For 
# target, when src is marked, it refers to the directory where the Docker image
# was built which in this case is assumed to be the top-level directory of 
# DuoLogSync. Install the necessary Python packages needed to test, lint, and 
# run DuoLogSync code
RUN --mount=type=bind,readwrite,target=/src \
        pip install -r /src/requirements.txt
