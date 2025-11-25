"""
Main application entry point for the Autonomous QA Agent.
This script initializes the Streamlit UI and communicates with the FastAPI backend
to handle knowledge base building, test case generation, and script creation.
"""

import streamlit as st
import requests
import json
import pandas as pd

# API Base URL
API_URL = "http://localhost:8000"

# Configure the Streamlit page with title and layout
st.set_page_config(page_title="Autonomous QA Agent", layout="wide")

st.title("Autonomous QA Agent")
st.markdown("### Test Case & Selenium Script Generator")

# Sidebar for Configuration
with st.sidebar:
    st.header("Configuration")
    # Try to get API key from secrets, handle case where secrets file doesn't exist
    default_api_key = ""
    try:
        default_api_key = st.secrets.get("GROQ_API_KEY", "")
    except FileNotFoundError:
        pass
    except Exception:
        pass # Handle other potential secret errors gracefully

    api_key = st.text_input("Groq API Key", type="password", help="Enter your Groq API Key", value=default_api_key)
    model_name = st.text_input("Model Name", value="llama-3.3-70b-versatile", help="e.g., llama-3.3-70b-versatile, mixtral-8x7b-32768")
    
    st.divider()
    st.info("Ensure the FastAPI backend is running on port 8000.")

# Initialize Session State variables to persist data across reruns
if 'kb_built' not in st.session_state:
    st.session_state.kb_built = False
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = []
if 'html_content' not in st.session_state:
    st.session_state.html_content = ""

# Define application tabs for different stages of the workflow
tab1, tab2, tab3 = st.tabs(["Knowledge Base", "Test Case Agent", "Selenium Agent"])

with tab1:
    st.header("1. Build Knowledge Base")
    st.markdown("Upload your support documents (Requirements, UI/UX, API) and the target HTML file.")
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded_files = st.file_uploader("Upload Support Docs", accept_multiple_files=True, type=['md', 'txt', 'json', 'pdf'])
    with col2:
        uploaded_html = st.file_uploader("Upload Target HTML", type=['html'])
    
    if st.button("Build Knowledge Base", type="primary"):
        if uploaded_files and uploaded_html:
            with st.spinner("Ingesting documents and building vector database..."):
                try:
                    # Prepare files for upload
                    files_to_upload = []
                    for f in uploaded_files:
                        files_to_upload.append(('files', (f.name, f.getvalue(), f.type)))
                    
                    # Prepare HTML file
                    html_file = ('html_file', (uploaded_html.name, uploaded_html.getvalue(), uploaded_html.type))
                    
                    # Store HTML content in session state
                    uploaded_html.seek(0)
                    st.session_state.html_content = uploaded_html.read().decode('utf-8')

                    # Correct way to send multiple files and a specific file in requests
                    # We need to reconstruct the files dictionary
                    multipart_files = []
                    for f in uploaded_files:
                        multipart_files.append(('files', (f.name, f.getvalue(), f.type)))
                    multipart_files.append(('html_file', (uploaded_html.name, uploaded_html.getvalue(), uploaded_html.type)))

                    response = requests.post(f"{API_URL}/ingest", files=multipart_files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Knowledge Base Built! Ingested {data['chunks']} chunks from {data['files']} files.")
                        st.session_state.kb_built = True
                    else:
                        st.error(f"Error building Knowledge Base: {response.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}. Is the backend running?")
        else:
            st.error("Please upload both support documents and the HTML file.")

with tab2:
    st.header("2. Generate Test Cases")
    if not st.session_state.kb_built:
        st.warning("Please build the Knowledge Base in Tab 1 first.")
    else:
        query = st.text_area("Enter Test Requirement", 
                             placeholder="e.g., 'Generate all positive and negative test cases for the discount code feature.'",
                             height=100)
        
        if st.button("Generate Test Cases", type="primary"):
            if not api_key:
                st.error("Please enter an API Key in the sidebar.")
            else:
                with st.spinner("Analyzing Knowledge Base and generating test cases..."):
                    try:
                        payload = {
                            "requirement": query,
                            "api_key": api_key,
                            "model": model_name
                        }
                        response = requests.post(f"{API_URL}/generate-test-cases", json=payload)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if isinstance(result, list) and len(result) > 0 and "error" in result[0]:
                                st.error(f"Error: {result[0]['error']}")
                            else:
                                st.session_state.test_cases = result
                                st.success(f"Generated {len(result)} test cases.")
                        else:
                            st.error(f"Error generating test cases: {response.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

        # Display Results
        if st.session_state.test_cases:
            st.subheader("Generated Test Cases")
            
            # Display as DataFrame for better readability
            df = pd.DataFrame(st.session_state.test_cases)
            st.dataframe(df, use_container_width=True)
            
            # Also show JSON for copy-paste
            with st.expander("View Raw JSON"):
                st.json(st.session_state.test_cases)

with tab3:
    st.header("3. Generate Selenium Script")
    if not st.session_state.kb_built:
        st.warning("Please build the Knowledge Base in Tab 1 first.")
    elif not st.session_state.test_cases:
        st.warning("Please generate test cases in Tab 2 first.")
    else:
        st.markdown("Select a test case to generate the automation script.")
        
        # Create a selection list
        test_case_options = [f"{tc.get('Test_ID', 'N/A')}: {tc.get('Test_Scenario', 'N/A')}" for tc in st.session_state.test_cases]
        selected_option = st.selectbox("Select Test Case", test_case_options)
        
        if st.button("Generate Selenium Script", type="primary"):
            if not api_key:
                st.error("Please enter an API Key in the sidebar.")
            else:
                # Find the selected test case object
                index = test_case_options.index(selected_option)
                selected_test_case = st.session_state.test_cases[index]
                
                with st.spinner("Generating Selenium Script..."):
                    try:
                        payload = {
                            "test_case": selected_test_case,
                            "html_content": st.session_state.html_content,
                            "api_key": api_key,
                            "model": model_name
                        }
                        response = requests.post(f"{API_URL}/generate-script", json=payload)
                        
                        if response.status_code == 200:
                            script = response.json().get("script", "")
                            st.subheader("Generated Python Script")
                            st.code(script, language="python")
                            st.success("Script Generated! Copy the code above.")
                        else:
                            st.error(f"Error generating script: {response.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")
