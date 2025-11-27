# Autonomous QA Agent

An intelligent, autonomous QA agent capable of constructing a "testing brain" from project documentation and generating test cases and Selenium scripts.

## Features
- **Knowledge Base Ingestion**: Ingests support documents (Markdown, Text, JSON) and HTML files into a Vector Database (ChromaDB).
- **Test Case Generation**: Uses RAG (Retrieval-Augmented Generation) to produce comprehensive test cases grounded in documentation.
- **Selenium Script Generation**: Converts generated test cases into executable Python Selenium scripts.
- **Streamlit UI**: A user-friendly interface for all operations.
- **REST API**: A FastAPI-based backend to expose agent functionalities programmatically.

## Setup Instructions

### Prerequisites
- Python 3.9+
- OpenAI API Key (or compatible LLM API Key)

### Installation
1. Clone the repository (or navigate to the project folder).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run
1. Start the Streamlit application:
   ```bash
   streamlit run src/main.py
   ```
2. The application will open in your browser at `http://localhost:8501`.

### Running the API
1. Start the FastAPI server:
   ```bash
   python src/api.py
   ```
2. The API will be available at `http://localhost:8000`.
3. Access the interactive API documentation (Swagger UI) at `http://localhost:8000/docs`.

## Usage Guide

### 1. Build Knowledge Base
- Go to the **"Knowledge Base"** tab.
- Upload the support documents (e.g., `product_specs.md`, `ui_ux_guide.txt`) and the target `checkout.html`.
- Click **"Build Knowledge Base"**.
- Wait for the success message.

### 2. Generate Test Cases
- Go to the **"Test Case Agent"** tab.
- Enter your OpenAI API Key in the sidebar.
- Enter a requirement (e.g., "Generate test cases for discount code").
- Click **"Generate Test Cases"**.
- View the generated test cases in the table or JSON view.

### 3. Generate Selenium Script
- Go to the **"Selenium Agent"** tab.
- Select one of the generated test cases from the dropdown.
- Click **"Generate Selenium Script"**.
- Copy the generated Python code and run it locally.

## API Reference (`src/api.py`)
The project now includes a REST API built with **FastAPI**, a modern, high-performance web framework for building APIs with Python. This allows you to integrate the QA Agent's capabilities into other workflows or applications.

### Endpoints
- **`POST /ingest`**: Uploads support documents and the target HTML file to build the knowledge base.
- **`POST /generate-test-cases`**: Generates test cases based on a text requirement.
- **`POST /generate-script`**: Generates a Selenium script for a specific test case.

## Included Assets
- `assets/checkout.html`: The target e-shop checkout page.
- `assets/product_specs.md`: Feature rules and specifications.
- `assets/ui_ux_guide.txt`: UI/UX guidelines.
- `assets/api_endpoints.json`: Mock API definitions.

## Project Structure
```
qa_agent/
├── assets/                 # Project assets
├── src/
│   ├── main.py             # Streamlit App
│   ├── backend.py          # Core logic (Ingestion, RAG, Generation)
│   ├── api.py              # FastAPI REST endpoints
├── requirements.txt
└── README.md
```
