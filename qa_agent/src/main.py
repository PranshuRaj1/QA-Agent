"""
Main application entry point for the Autonomous QA Agent.
This script initializes the Streamlit UI, handles user configuration,
and manages the workflow for building knowledge bases, generating test cases,
and creating Selenium automation scripts.
"""

import streamlit as st
import os
import json
import pandas as pd
from backend import KnowledgeBase, QAAgent

# Configure the Streamlit page with title and layout
st.set_page_config(page_title="Autonomous QA Agent", layout="wide")

st.title("Autonomous QA Agent")
st.markdown("### Test Case & Selenium Script Generator")

# Sidebar for Configuration
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Groq API Key", type="password", help="Enter your Groq API Key")
    model_name = st.text_input("Model Name", value="llama-3.3-70b-versatile", help="e.g., llama-3.3-70b-versatile, mixtral-8x7b-32768")
    
    st.divider()
    st.info("Ensure you have the dependencies installed and ChromaDB is working.")

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
                # Create a temporary directory to store uploaded files
                os.makedirs("temp", exist_ok=True)
                file_paths = []
                
                # Save uploaded support documents to the temp directory
                for uploaded_file in uploaded_files:
                    path = os.path.join("temp", uploaded_file.name)
                    with open(path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    file_paths.append(path)
                
                # Save the target HTML file to the temp directory
                html_path = os.path.join("temp", uploaded_html.name)
                with open(html_path, "wb") as f:
                    f.write(uploaded_html.getbuffer())
                    # Read HTML content into session state for later use by the Selenium Agent
                    uploaded_html.seek(0)
                    st.session_state.html_content = uploaded_html.read().decode('utf-8')
                
                file_paths.append(html_path)
                
                # Initialize Knowledge Base and ingest documents
                try:
                    kb = KnowledgeBase()
                    num_chunks = kb.ingest_documents(file_paths)
                    st.success(f"Knowledge Base Built! Ingested {num_chunks} chunks from {len(file_paths)} files.")
                    st.session_state.kb_built = True
                except Exception as e:
                    st.error(f"Error building Knowledge Base: {e}")
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
                    agent = QAAgent(api_key=api_key, model=model_name)
                    response = agent.generate_test_cases(query)
                    
                    if isinstance(response, list) and "error" in response[0]:
                         st.error(f"Error: {response[0]['error']}")
                    else:
                        st.session_state.test_cases = response
                        st.success(f"Generated {len(response)} test cases.")

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
                    agent = QAAgent(api_key=api_key, model=model_name)
                    script = agent.generate_selenium_script(selected_test_case, st.session_state.html_content)
                    
                    st.subheader("Generated Python Script")
                    st.code(script, language="python")
                    st.success("Script Generated! Copy the code above.")
