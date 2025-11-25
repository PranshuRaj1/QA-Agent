import os
import shutil
from typing import List, Dict, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from backend import KnowledgeBase, QAAgent

app = FastAPI(title="QA Agent API")

# --- Pydantic Models ---
class GenerateTestCasesRequest(BaseModel):
    requirement: str
    api_key: Optional[str] = None
    model: str = "llama-3.3-70b-versatile"

class GenerateScriptRequest(BaseModel):
    test_case: Dict
    html_content: str
    api_key: Optional[str] = None
    model: str = "llama-3.3-70b-versatile"

# --- Endpoints ---

@app.post("/ingest")
async def ingest_documents(
    files: List[UploadFile] = File(...),
    html_file: UploadFile = File(...)
):
    """
    Ingest support documents and the target HTML file into the Knowledge Base.
    """
    try:
        # Ensure temp directory exists
        os.makedirs("temp", exist_ok=True)
        file_paths = []

        # Save support files
        for file in files:
            path = os.path.join("temp", file.filename)
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            file_paths.append(path)

        # Save HTML file
        html_path = os.path.join("temp", html_file.filename)
        with open(html_path, "wb") as f:
            shutil.copyfileobj(html_file.file, f)
        file_paths.append(html_path)

        # Ingest
        kb = KnowledgeBase()
        num_chunks = kb.ingest_documents(file_paths)
        
        return {
            "message": "Ingestion successful", 
            "chunks": num_chunks, 
            "files": len(file_paths)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp files could be done here, but might be useful to keep for debugging
        pass

@app.post("/generate-test-cases")
async def generate_test_cases(request: GenerateTestCasesRequest):
    """
    Generate test cases based on requirements.
    """
    try:
        agent = QAAgent(api_key=request.api_key, model=request.model)
        test_cases = agent.generate_test_cases(request.requirement)
        return test_cases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-script")
async def generate_script(request: GenerateScriptRequest):
    """
    Generate a Selenium script for a specific test case.
    """
    try:
        agent = QAAgent(api_key=request.api_key, model=request.model)
        script = agent.generate_selenium_script(request.test_case, request.html_content)
        return {"script": script}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
