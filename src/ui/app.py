import streamlit as st
import requests
import os

API_URL = "http://127.0.0.1:5000"

st.title("🧾 Smart Grocery Bill Analyzer")

st.markdown("""
Upload your grocery bill image, and let AI extract item names, prices, and categories.  
Ask questions about your spending, find insights, and get grocery suggestions!
""")

# ✅ Ensure `temp/` directory exists before saving files
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)  # Create directory if it doesn’t exist

# ✅ Maintain state for bill processing
if "processed_bills" not in st.session_state:
    st.session_state["processed_bills"] = {}
if "grocery_data" not in st.session_state:
    st.session_state["grocery_data"] = []  # Store extracted bill data


# File Upload
uploaded_file = st.file_uploader("📤 Upload Your Grocery Bill Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    file_path = os.path.join(TEMP_DIR, uploaded_file.name)

    # ✅ Save the file inside `temp/` directory
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.image(uploaded_file, caption="Uploaded Bill", use_column_width=True)
    if st.button("📜 Process Bill"):
        if file_path in st.session_state["processed_bills"]:
            st.warning("⚠️ This bill has already been processed!")
        else:
            with st.spinner("Processing..."):
                files = {"file": open(file_path, "rb")}
                response = requests.post(f"{API_URL}/upload_bill", files=files)

            if response.status_code == 200:
                try:
                    data = response.json()["data"]
                    st.success("✅ Bill processed successfully!")
                     # ✅ Store bill data globally for future queries
                    st.session_state["processed_bills"][file_path] = data  
                    st.session_state["grocery_data"].extend(data)  # ✅ Store all processed items
                    st.subheader("📋 Extracted Grocery Data")
                    st.dataframe(data)

                    st.subheader("📊 Spending by Category")
                    categories = list(set([item["category"] for item in data]))

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

                except requests.exceptions.JSONDecodeError:
                    st.error("❌ Failed to parse JSON response from API.")
            else:
                st.error("❌ Error processing the bill. Please try again.")

# AI Chatbot
st.subheader("💬 Ask AI About Your Grocery Data")
user_question = st.text_input("Type your question here...")
if st.button("🤖 Ask AI"):
    if user_question:
        with st.spinner("Thinking..."):
            response = requests.post(f"{API_URL}/ask", json={
                "question": user_question,
                "history": st.session_state["grocery_data"]  # ✅ Pass processed data for reference
            })
        
        if response.status_code == 200:
            try:
                st.write("🤖 AI Response:")
                st.write(response.json()["response"])
            except requests.exceptions.JSONDecodeError:
                st.warning("⚠️ AI response was invalid. Please try again.")
        else:
            st.error("❌ Failed to process question.")
