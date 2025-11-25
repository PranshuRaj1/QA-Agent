#!/bin/bash

# Navigate to source directory where the app code lives
cd src

# 1. Start the FastAPI backend in the background
# We use nohup to keep it running and & to push it to background
nohup uvicorn api:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# Wait a few seconds for the backend to start
sleep 5

# 2. Start the Streamlit Frontend
# Hugging Face Spaces expects the app to run on port 7860
streamlit run main.py --server.port 7860 --server.address 0.0.0.0
