import os
import json
import shutil
import time
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader, 
    TextLoader, 
    JSONLoader,
    UnstructuredHTMLLoader
)
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_groq import ChatGroq
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()



class KnowledgeBase:
    """
    Manages the ingestion and retrieval of documents using ChromaDB.
    """
    def __init__(self, persist_directory="db"):
        """
        Initialize the KnowledgeBase.
        
        Args:
            persist_directory (str): Directory to store the ChromaDB database.
        """
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use local embeddings. This works without an API key.
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            
        self.collection = self.client.get_or_create_collection(
            name="qa_agent_kb",
            embedding_function=self.embedding_fn
        )

    def ingest_documents(self, file_paths: List[str]):
        """
        Ingest documents from the specified file paths into the vector database.
        
        Args:
            file_paths (List[str]): List of paths to files to be ingested.
            
        Returns:
            int: Number of chunks ingested.
        """
        documents = []
        for path in file_paths:
            try:
                ext = os.path.splitext(path)[1].lower()
                if ext == ".md":
                    loader = UnstructuredMarkdownLoader(path)
                    documents.extend(loader.load())
                elif ext == ".txt":
                    loader = TextLoader(path)
                    documents.extend(loader.load())
                elif ext == ".json":
                    # Custom JSON loading to keep it simple and text-based
                    with open(path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    documents.append(Document(page_content=json.dumps(content, indent=2), metadata={"source": path}))
                elif ext == ".html":
                    # Load HTML content
                     with open(path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                        # We want the structure too, not just text, so we might keep some tags or just raw text
                        # For RAG, raw text with some structure is usually fine.
                        text = soup.get_text(separator='\n')
                        documents.append(Document(page_content=text, metadata={"source": path}))
            except Exception as e:
                print(f"Error loading {path}: {e}")
        
        if not documents:
            return 0

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        ids = [f"doc_{os.path.basename(chunk.metadata.get('source', 'unknown'))}_{i}" for i, chunk in enumerate(chunks)]
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        if texts:
            # Clear existing to avoid duplicates in this simple implementation
            try:
                self.collection.delete(where={}) 
            except:
                pass
            
            # Add in batches with delay to avoid rate limits
            batch_size = 5
            for i in range(0, len(ids), batch_size):
                end = min(i + batch_size, len(ids))
                self.collection.add(ids=ids[i:end], documents=texts[i:end], metadatas=metadatas[i:end])
                time.sleep(1) # Sleep 1s between batches
        
        return len(chunks)

    def query(self, query_text: str, n_results: int = 5):
        """
        Query the knowledge base for relevant documents.
        
        Args:
            query_text (str): The query string.
            n_results (int): Number of results to return.
            
        Returns:
            dict: Query results from ChromaDB.
        """
        results = self.collection.query(query_texts=[query_text], n_results=n_results)
        return results

class QAAgent:
    """
    Agent responsible for generating test cases and Selenium scripts using LLMs.
    """
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the QAAgent.
        
        Args:
            api_key (str, optional): API Key for the LLM.
            model (str): Model name to use.
        """
        if not api_key:
            api_key = os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")
            
        self.kb = KnowledgeBase()
        
        # Configure LLM (Groq only)
        self.llm = ChatGroq(
            model=model,
            api_key=api_key,
            temperature=0.2
        )

    def generate_test_cases(self, requirement: str) -> List[Dict]:
        """
        Generate test cases based on the provided requirement and knowledge base context.
        
        Args:
            requirement (str): The test requirement description.
            
        Returns:
            List[Dict]: A list of generated test cases.
        """
        # 1. Retrieve context
        context_results = self.kb.query(requirement)
        context_docs = context_results['documents'][0]
        context_sources = [m['source'] for m in context_results['metadatas'][0]]
        
        context_str = ""
        for doc, source in zip(context_docs, context_sources):
            context_str += f"--- Source: {os.path.basename(source)} ---\n{doc}\n\n"
        
        # 2. Construct Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert QA Test Engineer. Your goal is to generate comprehensive test cases based strictly on the provided project documentation.
            
            Rules:
            1. Ground all test cases in the provided context.
            2. Do not hallucinate features not mentioned in the context.
            3. Output must be a valid JSON list of objects.
            4. Each object must have: "Test_ID", "Feature", "Test_Scenario", "Expected_Result", "Grounded_In" (filename).
            """),
            ("user", """Context:
            {context}
            
            Requirement:
            {requirement}
            
            Generate test cases in JSON format:
            """)
        ])
        
        # 3. Chain
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            result = chain.invoke({"context": context_str, "requirement": requirement})
            return result
        except Exception as e:
            return [{"error": str(e)}]

    def generate_selenium_script(self, test_case: Dict, html_content: str) -> str:
        """
        Generate a Selenium Python script for a specific test case.
        
        Args:
            test_case (Dict): The test case details.
            html_content (str): The HTML content of the target page.
            
        Returns:
            str: The generated Python script.
        """
        # 1. Construct Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Selenium Python Automation Engineer.
            Your task is to write a robust, runnable Python Selenium script for a specific test case.
            
            Target HTML Content:
            {html_content}
            
            Rules:
            1. **Driver Setup**: Do NOT use 'webdriver_manager'. Use built-in Selenium Manager: `driver = webdriver.Chrome()`.
            2. **File Loading**: Assume the target file is named 'index.html' in the same directory. Use `os.path.abspath("index.html")` combined with the `file:///` prefix to load it. Example: `driver.get("file:///" + os.path.abspath("index.html"))`.
            3. **Color Assertions**: Import `from selenium.webdriver.support.color import Color`. Convert CSS colors to Hex for comparison (e.g., `assert Color.from_string(elem.value_of_css_property('color')).hex == '#ff0000'`).
            4. **Clean Code**: Do NOT import unused libraries like `math` or `webdriver_manager`. Keep imports minimal.
            5. **Visual Feedback**: Add `print("SUCCESS: Test Case [Name] Passed")` at the very end of the script.
            6. **Waits & Selectors**: Use `WebDriverWait` and robust selectors (ID, CSS) that exist in the HTML.
            7. **Output**: Return ONLY the Python code, no markdown formatting like ```python.
            
            Robustness Guidelines:
            - Data Parsing: When parsing currency (e.g., "$100.00"), remove non-numeric characters before converting to float. Handle empty strings gracefully.
            - Assertions: Use 'in' for text checks instead of '==' (e.g., "Discount Applied" in message). Use round() for float comparisons if needed.
            - Selectors: Prefer IDs or data attributes over text content.
            """),
            ("user", """Test Case:
            {test_case}
            
            Generate the Python Selenium script:
            """)
        ])
        
        # 2. Chain
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({"html_content": html_content, "test_case": json.dumps(test_case, indent=2)})
            # Clean up markdown if present
            result = result.replace("```python", "").replace("```", "").strip()
            return result
        except Exception as e:
            return f"# Error generating script: {str(e)}"
