# Use Python 3.9 (ChromaDB works best with 3.9/3.10)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for SQLite/ChromaDB)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Overwrite default sqlite3 with pysqlite3-binary (Fix for ChromaDB on old Linux distros)
# This is a common fix required for ChromaDB in Docker containers
RUN pip install pysqlite3-binary
# NOTE: The path below might vary depending on python version/distro, but this is a common hack.
# A more robust way is to do this in python code before importing chromadb.
RUN echo 'import sys; import pysqlite3; sys.modules["sqlite3"] = pysqlite3' >> /usr/local/lib/python3.9/site-packages/google/colab/__init__.py || true

# Copy application code
COPY . .

# Grant execution permissions to the start script
RUN chmod +x start.sh

# Expose the port Hugging Face expects
EXPOSE 7860

# Run the start script
CMD ["./start.sh"]
