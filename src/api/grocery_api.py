from flask import Flask, request, jsonify
from flask_cors import CORS
import os, uuid, re, json
from src.ocr.ocr_extractor import extract_text_easyocr
from src.parsing.langchain_parser import parse_grocery_bill
from src.knowledge_graph.neo4j_connector import GroceryGraph, get_existing_labels_and_relationships
from src.knowledge_graph.query_handler import query_total_spent  # if needed
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

grocery_graph = GroceryGraph()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Load OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing. Please set it in the environment variables.")

# Initialize OpenAI model globally
openai_model = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY, temperature=0)

# Initialize conversation memory
#memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

class MemoryManager:
    def __init__(self, max_messages=4, memory_file="memory.json"):
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.max_messages = max_messages
        self.memory_file = memory_file
        self.session_id = str(uuid.uuid4())[:8]  # Generate a unique session ID
        self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.session_id = data.get('session_id', self.session_id)
                    messages = data.get('messages', [])
                    for msg in messages:
                        if msg['type'] == 'human':
                            self.memory.chat_memory.add_message(HumanMessage(content=msg['content']))
                        else:
                            self.memory.chat_memory.add_message(AIMessage(content=msg['content']))
            except Exception as e:
                print(f"Error loading memory: {e}")

    def save_memory(self):
        try:
            messages = []
            for msg in self.memory.chat_memory.messages:
                messages.append({
                    'type': 'human' if isinstance(msg, HumanMessage) else 'ai',
                    'content': msg.content,
                    'timestamp': datetime.now().isoformat()
                })
            
            with open(self.memory_file, 'w') as f:
                json.dump({
                    'session_id': self.session_id,
                    'messages': messages,
                    'last_updated': datetime.now().isoformat()
                }, f)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def add_message(self, message, is_human=True):
        # Check if we need to remove old messages
        while len(self.memory.chat_memory.messages) >= self.max_messages:
            self.memory.chat_memory.messages.pop(0)
        
        if is_human:
            self.memory.chat_memory.add_message(HumanMessage(content=message))
        else:
            self.memory.chat_memory.add_message(AIMessage(content=message))
        
        self.save_memory()

    def get_memory(self):
        return self.memory.load_memory_variables({})["chat_history"]

    def clear_memory(self):
        self.memory.clear()
        self.session_id = str(uuid.uuid4())[:8]  # Generate a new session ID
        self.save_memory()

# Initialize memory manager
memory_manager = MemoryManager()

def format_query_result(records, user_question):
    """Uses retrieved Neo4j records to generate a conversational answer."""
    if not records:
        return "No relevant data found in your grocery history."

    rag_prompt = f"""
    You are an AI assistant summarizing grocery spending data.
    The user asked: "{user_question}"
    Here are the raw query results from the grocery database:
    {json.dumps(records, indent=2)}

    Generate a clear and concise answer for the user.
    """
    response = openai_model.predict(rag_prompt).strip()
    return response

def validate_cypher_query(query, labels, relationships, properties):
    """Ensures Cypher query only uses valid labels, relationships, and properties."""
    
    for label in labels:
        if re.search(rf"\b{label}\.", query):
            props_in_query = re.findall(rf"{label}\.([a-zA-Z0-9_]+)", query)
            for prop in props_in_query:
                if prop not in properties.get(label, []):
                    print(f"⚠️ Invalid property detected: {label}.{prop}")
                    return False  # Query is invalid

    for relationship in relationships:
        if relationship not in query:
            print(f"⚠️ Missing relationship: {relationship}")

    return True  # Query is valid

def get_existing_labels_and_relationships(driver):
    """Fetches valid labels, relationships, and properties from Neo4j to prevent invalid queries."""
    with driver.session() as session:
        labels_result = session.run("CALL db.labels() YIELD label RETURN COLLECT(label) AS labels")
        relationships_result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN COLLECT(relationshipType) AS relationships")
        properties_result = session.run("CALL db.schema.nodeTypeProperties() YIELD nodeLabels, propertyName RETURN nodeLabels, COLLECT(propertyName) AS properties")

        labels = labels_result.single()["labels"]
        relationships = relationships_result.single()["relationships"]
        properties = {row["nodeLabels"][0]: row["properties"] for row in properties_result}

        return labels, relationships, properties

def generate_cypher_query(user_question, labels, relationships, properties):
    """Generates a Cypher query based on the question and valid schema."""
    
    cypher_prompt = f"""
    You are an AI assistant with access to a grocery spending knowledge graph (Neo4j).
    The user asked: "{user_question}"

    Use **only** these valid schema elements:
    - **Node Labels:** {labels}
    - **Relationships:** {relationships}
    - **Properties for Each Label:** {json.dumps(properties, indent=2)}

    ⚠️ **Rules:**
    - **Do not use any properties that are not listed above.**
    - Ensure **case-insensitive matching** for categories using `toLower()`.
    - **Alias aggregations** like `SUM(i.price) AS total_spent`.
    - **Ensure relationships exist** before using them in the query.
    - **If querying multiple categories**, use `WHERE toLower(c.name) IN ['category1', 'category2']`.

    ### Example Queries:
    - "What is my most expensive item?" → 
      ```cypher
      MATCH (u:User {{name: 'Sanjana'}})-[:BOUGHT]->(i:Item)
      RETURN i.name, i.price ORDER BY i.price DESC LIMIT 1
      ```
    - "On what did I spend the most?" → 
      ```cypher
      MATCH (u:User {{name: 'Sanjana'}})-[:BOUGHT]->(i:Item)-[:BELONGS_TO]->(c:Category)
      RETURN c.name, SUM(i.price) AS total_spent ORDER BY total_spent DESC LIMIT 1
      ```
    - "How much did I spend on produce, bakery, and snacks?" →
      ```cypher
      MATCH (u:User {{name:'Sanjana'}})-[:BOUGHT]->(i:Item)-[:BELONGS_TO]->(c:Category)
      WHERE toLower(c.name) IN ['produce', 'bakery', 'snacks']
      RETURN SUM(i.price) AS total_spent
      ```
    - "What item do I buy the most?" →
      ```cypher
      MATCH (u:User {{name: 'Sanjana'}})-[r:BOUGHT]->(i:Item)
      RETURN i.name, SUM(r.quantity) AS item_freq ORDER BY item_freq DESC LIMIT 1
      ```

    **Output only the Cypher query.**
    """

    cypher_query = openai_model.predict(cypher_prompt).strip().strip("`").strip('"')

    # ✅ Ensure category names are case-insensitive
    cypher_query = re.sub(r"\{name: '([^']+)'\}", r"{name: toLower('\1')}", cypher_query)

    # ✅ Ensure aliasing is done properly
    cypher_query = re.sub(r"AS total_spent\s+AS\s+\w+", "AS total_spent", cypher_query)

    print(f"🔍 Generated Cypher Query:\n{cypher_query}")  # Debugging
    return cypher_query

# -------------------------
# Helper: Execute Cypher query and return results
def execute_cypher_query(cypher_query):
    """Executes a Cypher query and returns the results."""
    try:
        with grocery_graph.driver.session() as session:
            result = session.run(cypher_query)
            records = result.data()
            print(f"🔍 Query Results: {records}")
            return records if records else None
    except Exception as e:
        print(f"❌ Cypher Execution Error: {str(e)}")
        return None

# -------------------------
# Helper: Check history for answer using conversation buffer
def check_history_for_answer(user_question, past_messages):
    """Generates a response from past conversation history if relevant."""
    if not past_messages:
        return None
    history_text = "\n".join([msg.content for msg in past_messages])
    history_prompt = f"""
    The user asked: "{user_question}"
    Based on the following past conversation history:
    {history_text}
    
    Provide a concise answer using the historical data.
    """
    response = openai_model.predict(history_prompt).strip()
    return response if response else None

# -------------------------
# /upload_bill endpoint 
@app.route("/upload_bill", methods=["POST"])
def upload_bill():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    extracted_text = extract_text_easyocr(file_path)
    structured_data = parse_grocery_bill(extracted_text)
    if isinstance(structured_data, dict) and "items" in structured_data:
        structured_data = structured_data["items"]
    if not isinstance(structured_data, list):
        return jsonify({"error": "Parsed data is not a valid list"}), 500
    for entry in structured_data:
        if "name" in entry:
            entry["item"] = entry.pop("name")

    print("Final Structured Data:", structured_data)
    bill_id = str(uuid.uuid4())[:8]
    grocery_graph.store_grocery_data("Sanjana", structured_data, bill_id)
    return jsonify({"message": "Bill processed successfully!", "bill_id": bill_id, "data": structured_data})


#@app.route("/spending/<category>", methods=["GET"])
@app.route("/spending/<path:category>", methods=["GET"])
def get_spending(category):
    total_spent = query_total_spent(category)
    return jsonify({"category": category, "total_spent": total_spent})


@app.route("/ask", methods=["POST"])
def ask_question():
    """Handles user queries dynamically using intent classification, Neo4j, and AI."""
    data = request.json
    user_question = data.get("question", "").strip().lower()

    if not user_question:
        return jsonify({"error": "Question cannot be empty."}), 400

    # Add user question to memory
    memory_manager.add_message(user_question, is_human=True)

    # Fetch Schema from Neo4j **only once**
    labels, relationships, properties = get_existing_labels_and_relationships(grocery_graph.driver)

    # Generate Cypher Query Using Only Valid Schema
    cypher_query = generate_cypher_query(user_question, labels, relationships, properties)

    # Validate Query Before Execution
    if not validate_cypher_query(cypher_query, labels, relationships, properties):
        return jsonify({"error": "Generated query contains invalid fields. Please refine your question."}), 400

    # Check Memory for Previously Asked Questions
    past_conversations = memory_manager.get_memory()
    print(f"🧠 Stored Memory: {past_conversations}")  # Debugging

    for i, past in enumerate(past_conversations):
        if hasattr(past, "role") and past.role == "human" and user_question in past.content.lower():
            if i + 1 < len(past_conversations) and getattr(past_conversations[i + 1], "role", None) == "ai":
                print("🔍 Reusing previous query intent from memory.")
                return jsonify({"response": past_conversations[i + 1].content})

    # Intent Classification using AI
    intent_prompt = f"""
    You are an AI assistant analyzing grocery spending.
    The user asked: "{user_question}"
    
    Determine the intent from the following options:
    - "database_query": if the question requires querying Neo4j.
    - "session_data": if the question can be answered from past conversation history.
    - "rag": if the question needs both Neo4j and past conversation data.
    - "ai_inference": if no structured data is available, generate an answer using general knowledge.
    
    Output only one of: "database_query", "session_data", "rag", or "ai_inference".
    """
    intent = openai_model.predict(intent_prompt).strip().strip('"')
    print(f"🔍 AI Intent Prediction: {intent}")

    if intent in ["database_query", "rag"]:
        records = execute_cypher_query(cypher_query)
        if records:
            # RAG: Combine DB Data + Memory Context
            rag_prompt = f"""
            The user asked: "{user_question}"
            
            Here is the data retrieved from the database:
            {json.dumps(records, indent=2)}
            
            Here is the past conversation history:
            {json.dumps([msg.content for msg in past_conversations], indent=2)}
            
            Generate a clear, detailed, and conversational answer based on this information.
            """
            ai_response = openai_model.predict(rag_prompt).strip()
            memory_manager.add_message(ai_response, is_human=False)
            return jsonify({"response": ai_response})

    elif intent == "session_data":
        history_response = check_history_for_answer(user_question, past_conversations)
        if history_response:
            memory_manager.add_message(history_response, is_human=False)
            return jsonify({"response": history_response})

    elif intent == "ai_inference":
        ai_fallback_prompt = f"""
        The user asked: "{user_question}"
        Generate an answer based solely on general grocery spending knowledge.
        """
        fallback_response = openai_model.predict(ai_fallback_prompt).strip()
        memory_manager.add_message(fallback_response, is_human=False)
        return jsonify({"response": fallback_response})
    
    return jsonify({"response": "I'm not sure how to answer that. Could you clarify?"})


# Endpoint to check conversation memory
@app.route("/memory", methods=["GET"])
def get_memory():
    memory_data = memory_manager.get_memory()
    return jsonify({
        "chat_history": [msg.content for msg in memory_data],
        "session_id": memory_manager.session_id,
        "message_count": len(memory_data)
    })

if __name__ == "__main__":
    app.run(debug=True)
