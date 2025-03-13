from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from src.ocr.ocr_extractor import extract_text_easyocr
from src.parsing.langchain_parser import parse_grocery_bill
from src.knowledge_graph.neo4j_connector import GroceryGraph
from src.knowledge_graph.query_handler import query_total_spent
from langchain.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.chat_models import ChatOpenAI
import requests
import uuid
import re

app = Flask(__name__)
CORS(app)  # Allow frontend to communicate with API

grocery_graph = GroceryGraph()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the directory exists
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ✅ Load OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing. Please set it in the environment variables.")

# ✅ Initialize OpenAI Model Globally
openai_model = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY)

@app.route("/")
def home():
    return jsonify({"message": "Welcome to Grocery API!"})

@app.route("/upload_bill", methods=["POST"])
def upload_bill():
    """Handles grocery bill image upload and processing."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)

    # Step 1: Extract text using OCR
    extracted_text = extract_text_easyocr(file_path)

    # Step 2: Parse the extracted text into structured JSON
    structured_data = parse_grocery_bill(extracted_text)

    # ✅ Extract the list from `structured_data`
    if isinstance(structured_data, dict) and "items" in structured_data:
        structured_data = structured_data["items"]  # ✅ Extract the list

    if not isinstance(structured_data, list) or not all(isinstance(entry, dict) for entry in structured_data):
        return jsonify({"error": "Parsed data is not a valid list"}), 500
    
    # ✅ Fix: Ensure key renaming only happens if "name" exists
    for entry in structured_data:
        if "name" in entry:
            entry["item"] = entry.pop("name")  # Rename "name" -> "item"


    # Debugging: Print structured data before storing
    print("Final Structured Data:", structured_data)

    # ✅ Generate a unique bill ID
    bill_id = str(uuid.uuid4())[:8]

    grocery_graph.store_grocery_data("Sanjana", structured_data, bill_id)

    return jsonify({"message": "Bill processed successfully!", "bill_id": bill_id, "data": structured_data})



@app.route("/spending/<category>", methods=["GET"])
def get_spending(category):
    """Fetches total spending for a category."""
    total_spent = query_total_spent(category)
    return jsonify({"category": category, "total_spent": total_spent})

'''
@app.route("/ask", methods=["POST"])
def ask_question():
    """Handles user queries about grocery spending, dynamically selecting the right data source."""
    data = request.json
    user_question = data.get("question", "").lower()

    if not user_question:
        return jsonify({"error": "Question cannot be empty."}), 400

    # ✅ Step 1: Let GPT Decide How to Answer the Question
    query_decision_prompt = f"""
    You are an AI assistant with access to a grocery spending knowledge graph (Neo4j).

    The user asked: "{user_question}"

    Available API Endpoints for Data Retrieval:
    1️⃣ /spending/total → Returns total grocery spending.
    2️⃣ /spending/<category> → Returns total spending in a specific category.
    3️⃣ /most_expensive_item → Returns the most expensive item purchased.
    4️⃣ /cheapest_item → Returns the least expensive item purchased.
    5️⃣ /most_purchased_item → Returns the most frequently purchased item.
    6️⃣ /items_in_category/<category> → Returns a list of all items in a given category.
    7️⃣ /savings_tips → Returns budget-friendly grocery tips.

    🎯 Your Task:
    - Determine which API call (if any) should be used to answer the question.
    - If multiple APIs could be used, choose the most relevant one.
    - If the question doesn't require database retrieval, generate a useful response yourself.
    - If calling an API, respond with only the endpoint URL (e.g., "/spending/fruits").

    Do NOT return anything except a single API path or a direct answer.
    """

    gpt_response = openai_model.predict(query_decision_prompt).strip()

    # ✅ Step 2: Check if GPT returned an API call
    if gpt_response.startswith("/"):  # If GPT suggests an API call
        api_endpoint = f"http://127.0.0.1:5000{gpt_response}"
        res = requests.get(api_endpoint)

        if res.status_code == 200:
            api_data = res.json()
            return jsonify({"response": format_api_response(api_data, gpt_response)})
        else:
            return jsonify({"response": f"Sorry, I couldn't fetch the data for {gpt_response}."})

    else:
        # ✅ GPT provided a direct answer, return as-is
        return jsonify({"response": gpt_response})

def format_api_response(api_data, endpoint):
    """Formats API response for better readability."""
    if "/spending/" in endpoint:
        category = endpoint.split("/")[-1]
        return f"You spent ${api_data.get('total_spent', 0.0):.2f} on {category}."
    elif "/most_expensive_item" in endpoint:
        return f"Your most expensive item was {api_data['item']} costing ${api_data['price']:.2f}."
    elif "/cheapest_item" in endpoint:
        return f"Your cheapest item was {api_data['item']} costing ${api_data['price']:.2f}."
    elif "/most_purchased_item" in endpoint:
        return f"Your most purchased item is {api_data['item']}, which you bought {api_data['quantity']} times."
    elif "/items_in_category/" in endpoint:
        category = endpoint.split("/")[-1]
        items = ", ".join(api_data.get("items", []))
        return f"Items in {category}: {items}."
    elif "/savings_tips" in endpoint:
        return f"Here are some budget-friendly grocery tips: {api_data.get('tips', 'No tips available.')}"
    return "Data retrieved, but couldn't format the response."

'''


@app.route("/ask", methods=["POST"])
def ask_question():
    """Handles user queries dynamically using Neo4j and GPT."""
    data = request.json
    user_question = data.get("question", "").lower()
    history = data.get("history", []) 

    if not user_question:
        return jsonify({"error": "Question cannot be empty."}), 400
    
    # ✅ Step 1: Check if the answer is available in `history`
    history_response = check_history_for_answer(user_question, history)
    if history_response:
        return jsonify({"response": history_response})


    # ✅ Step 1: Ask GPT to generate the Cypher query
    cypher_prompt = f"""
    You are an AI assistant with access to a grocery spending knowledge graph (Neo4j).
    The user asked: "{user_question}"

    Generate an optimized Cypher query based on the question intent:
    - If the question asks for "on what did I spend the most?", sum spending per category and return the highest one.
    - If the question asks for "how much did I spend on X category?", sum the price of items belonging to that category.
    - If the question asks for "what is my most expensive item?", order by price and return the top item.
    - If the question asks for "what item do I buy the most?", count the occurrences of items and return the most frequent one.
    
    Database Schema:
    - (:User)-[:BOUGHT]->(:Item)-[:BELONGS_TO]->(:Category)
    - User nodes contain `name`
    - Item nodes contain `name` and `price`
    - Category nodes contain `name`

    Example Inputs & Expected Cypher Queries:
    - "On what did I spend the most?" → `MATCH (u:User {{name: 'Sanjana'}})-[:BOUGHT]->(i:Item)-[:BELONGS_TO]->(c:Category) RETURN c.name, SUM(i.price) AS total_spent ORDER BY total_spent DESC LIMIT 1`
    - "How much did I spend on Fruits?" → `MATCH (u:User {{name: 'Sanjana'}})-[:BOUGHT]->(i:Item)-[:BELONGS_TO]->(c:Category {{name: 'Fruits'}}) RETURN SUM(i.price) AS total_spent`
    - "What is my most expensive item?" → `MATCH (u:User {{name: 'Sanjana'}})-[:BOUGHT]->(i:Item) RETURN i.name, i.price ORDER BY i.price DESC LIMIT 1`
    - "What item do I buy the most?" → `MATCH (u:User {{name: 'Sanjana'}})-[:BOUGHT]->(i:Item) RETURN i.name, COUNT(i) AS frequency ORDER BY frequency DESC LIMIT 1`

    Output only the Cypher query.
    """

    #cypher_query = openai_model.predict(cypher_prompt).strip()
    cypher_query = openai_model.predict(cypher_prompt).strip().strip("`").strip('"')
    #cypher_query = cypher_query.replace("{name: '", "{name: toLower('")
    cypher_query = re.sub(r"\{name: '([^']+)'\}", r"{name: toLower('\1')}", cypher_query)
    
    print(f"🔍 Generated Cypher Query:\n{cypher_query}")  # ✅ Log query for debugging

    # ✅ Step 2: Execute the generated Cypher query
    try:
        with grocery_graph.driver.session() as session:
            result = session.run(cypher_query)
            records = result.data()
            
            print(f"🔍 Query Results: {records}")  # ✅ Log query results
            
            if records:
                return jsonify({"response": format_query_result(records, user_question)})
            else:
                return jsonify({"response": "No relevant data found in your grocery history."})
    except Exception as e:
        print(f"❌ Cypher Execution Error: {str(e)}")  # ✅ Log the exact error
        return jsonify({"error": f"Failed to execute query: {str(e)}"}), 500

def check_history_for_answer(user_question, history):
    """Checks processed bills for relevant information before querying Neo4j."""
    
    if not history:
        return None  # ✅ No past processed data
    
    if "most expensive item" in user_question:
        # ✅ Find the most expensive item in history
        most_expensive = max(history, key=lambda x: float(x["price"]), default=None)
        if most_expensive:
            return f"Your most expensive item was {most_expensive['item']} costing ${most_expensive['price']}."

    elif "most purchased item" in user_question:
        # ✅ Find the most frequently purchased item
        item_counts = {}
        for entry in history:
            item_counts[entry["item"]] = item_counts.get(entry["item"], 0) + int(entry["quantity"])
        
        most_purchased = max(item_counts, key=item_counts.get, default=None)
        if most_purchased:
            return f"Your most purchased item is {most_purchased}, bought {item_counts[most_purchased]} times."

    elif "spend on" in user_question:
        # ✅ Find total spent on a category
        category_name = user_question.split("spend on")[-1].strip().lower()
        total_spent = sum(float(entry["price"]) for entry in history if entry["category"].lower() == category_name)

        if total_spent > 0:
            return f"You spent ${total_spent:.2f} on {category_name}."

    return None  # ✅ If no relevant data found in history

def format_query_result(records, user_question):
    """Formats the database query results into a readable response."""
    if "spend the most" in user_question:
        return f"You spent the most on {records[0]['c.name']}, totaling ${records[0]['total_spent']:.2f}."
    elif "spend on" in user_question:
        return f"You spent ${records[0]['total_spent']:.2f} on this category."
    elif "most expensive item" in user_question:
        return f"Your most expensive item was {records[0]['i.name']} costing ${records[0]['i.price']:.2f}."
    elif "most purchased item" in user_question:
        return f"Your most purchased item is {records[0]['i.name']}, bought {records[0]['frequency']} times."
    else:
        return f"Here’s what I found: {records}"

if __name__ == "__main__":
    app.run(debug=True)
