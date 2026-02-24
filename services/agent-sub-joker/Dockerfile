# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM python:3.13-slim
ARG SVC_SLUG

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy the rest of the application's code
RUN mkdir -p /app/src

COPY ./libs /app/libs

# Copy only the requirements, to cache them in Docker layer
COPY ./services/${SVC_SLUG}/pyproject.toml /app/pyproject.toml

# Copy the rest of the application's code
COPY ./services/${SVC_SLUG}/src/ /app/src

# Install Python dependencies and module
RUN pip install -e .

# Run the application as a non-root user for security
RUN adduser --disabled-password --gecos "" user && chown -R user:user /app
USER user

WORKDIR /app/src

# Command to run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
