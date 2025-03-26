import streamlit as st
import requests
import os
from PIL import Image
import io

API_URL = "http://127.0.0.1:5000"

# Add custom CSS for the response container
st.markdown("""
<style>
    .ai-response {
        background-color: #2D2D2D;
        border-radius: 10px;
        padding: 25px;
        margin: 10px 0;
        border: 1px solid #444;
        font-size: 1.1em;
        line-height: 1.6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .stMarkdown {
        max-width: 100% !important;
    }
    /* Make containers wider */
    .block-container {
        max-width: 95% !important;
        padding: 2rem 5rem !important;
    }
    /* Style the response header */
    .response-header {
        font-size: 1.2em;
        margin-bottom: 15px;
        color: #4CAF50;
    }
    /* Hide empty containers */
    .element-container:empty {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧾 Smart Grocery Bill Analyzer")

st.markdown("""
Upload your grocery bill image, and let AI extract item names, prices, and categories.  
Ask questions about your spending, find insights, and get grocery suggestions!
""")

# ✅ Ensure `temp/` directory exists before saving files
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)  # Create directory if it doesn't exist

# ✅ Maintain state for bill processing
if "processed_bills" not in st.session_state:
    st.session_state["processed_bills"] = {}
if "grocery_data" not in st.session_state:
    st.session_state["grocery_data"] = []  # Store extracted bill data
if "show_data" not in st.session_state:
    st.session_state["show_data"] = False
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

# File Upload
uploaded_file = st.file_uploader("📤 Upload Your Grocery Bill Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    file_path = os.path.join(TEMP_DIR, uploaded_file.name)

    # ✅ Save the file inside `temp/` directory
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Display image in a column with controlled width
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(uploaded_file, caption="Uploaded Bill", width=400)

    if st.button("📜 Process Bill"):
        if file_path in st.session_state["processed_bills"]:
            st.warning("⚠️ This bill has already been processed!")
        else:
            with st.spinner("Processing..."):
                files = {"file": open(file_path, "rb")}
                response = requests.post(f"{API_URL}/upload_bill", files=files)

            if response.status_code == 200:
                try:
                    data = response.json()
                    st.success("Bill processed successfully!")
                    # Store bill data
                    st.session_state["processed_bills"][file_path] = data["data"]
                    st.session_state["grocery_data"].extend(data["data"])
                    st.session_state["show_data"] = True
                except requests.exceptions.JSONDecodeError:
                    st.error("Failed to parse JSON response from API.")
            else:
                st.error("Error processing the bill. Please try again.")

# Always show the data if it exists
if st.session_state["show_data"] and len(st.session_state["grocery_data"]) > 0:
    st.subheader("📋 Extracted Grocery Data")
    st.dataframe(st.session_state["grocery_data"])

    st.subheader("📊 Spending by Category")
    categories = list(set([item["category"] for item in st.session_state["grocery_data"]]))

    for category in categories:
        res = requests.get(f"{API_URL}/spending/{category}")
        
        if res.status_code == 200:
            try:
                total_spent = res.json().get("total_spent", 0.0)
                st.write(f"**{category}:** ${total_spent:.2f}")
            except requests.exceptions.JSONDecodeError:
                st.warning(f"⚠️ Could not parse spending data for {category}.")
        else:
            st.warning(f"⚠️ API request failed for category: {category}")

# AI Chatbot
st.subheader("💬 Ask AI About Your Grocery Data")

def process_question(question):
    if question:
        with st.spinner("Thinking..."):
            response = requests.post(f"{API_URL}/ask", json={
                "question": question
            })
        
        if response.status_code == 200:
            try:
                response_text = response.json()["response"]
                if response_text:  # Only show container if there's a response
                    response_container = st.container()
                    with response_container:
                        st.markdown(f"""
                        <div class="ai-response">
                            <div class="response-header">🤖 <strong>AI Response:</strong></div>
                            <div>{response_text}</div>
                        </div>
                        """, unsafe_allow_html=True)
            except requests.exceptions.JSONDecodeError:
                st.warning("⚠️ AI response was invalid. Please try again.")
        else:
            st.error("❌ Failed to process question.")
    else:
        st.warning("⚠️ Please enter a question.")

# Handle both button click and Enter key submission
user_question = st.text_input("Type your question here...", key="question_input")

# Make the Ask AI button more prominent
if st.button("🤖 Ask AI", use_container_width=True, type="primary"):
    process_question(user_question)

# Add a button to view conversation history
if st.button("📜 View Conversation History"):
    try:
        memory_response = requests.get(f"{API_URL}/memory")
        if memory_response.status_code == 200:
            memory_data = memory_response.json()
            st.subheader("Conversation History")
            
            # Show session information
            st.write(f"Session ID: {memory_data['session_id']}")
            st.write(f"Total Messages: {memory_data['message_count']}")
            
            # Show conversation history
            for msg in memory_data["chat_history"]:
                st.markdown(f"""
                <div class="ai-response">
                    <div>{msg}</div>
                </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Failed to fetch conversation history: {e}")

# Add a button to clear conversation history
if st.button("🗑️ Clear Conversation History"):
    try:
        memory_manager.clear_memory()
        st.success("Conversation history cleared!")
    except Exception as e:
        st.error(f"Failed to clear conversation history: {e}")