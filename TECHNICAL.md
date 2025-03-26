# Technical Documentation

## System Architecture

### 1. Frontend (Streamlit)
- **Location**: `src/ui/app.py`
- **Purpose**: User interface for bill upload and interaction
- **Key Components**:
  - File upload interface
  - Data display
  - Chat interface
  - Conversation history viewer

### 2. Backend (Flask)
- **Location**: `src/api/grocery_api.py`
- **Purpose**: API endpoints and business logic
- **Key Components**:
  - File upload handling
  - OCR processing
  - AI integration
  - Database operations
  - Memory management

### 3. OCR Processing
- **Location**: `src/ocr/ocr_extractor.py`
- **Technology**: EasyOCR
- **Process**:
  1. Image preprocessing
  2. Text extraction
  3. Post-processing for accuracy

### 4. AI Processing
- **Location**: `src/parsing/langchain_parser.py`
- **Technologies**:
  - GPT-4
  - LangChain
  - RAG (Retrieval Augmented Generation)
- **Process**:
  1. Text parsing
  2. Structured data extraction
  3. Category inference
  4. Query understanding
  5. Response generation

### 5. Database (Neo4j)
- **Location**: `src/knowledge_graph/neo4j_connector.py`
- **Schema**:
  ```cypher
  (User)-[:BOUGHT]->(Item)
  (Item)-[:BELONGS_TO]->(Category)
  (Bill)-[:CONTAINS]->(Item)
  ```
- **Key Operations**:
  - Data storage
  - Query execution
  - Relationship management

## Implementation Details

### 1. Bill Processing Pipeline

```python
# 1. Image Upload
@app.route("/upload_bill", methods=["POST"])
def upload_bill():
    file = request.files["file"]
    file_path = save_file(file)
    
    # 2. OCR Processing
    extracted_text = extract_text_easyocr(file_path)
    
    # 3. AI Parsing
    structured_data = parse_grocery_bill(extracted_text)
    
    # 4. Database Storage
    bill_id = generate_bill_id()
    store_grocery_data(user, structured_data, bill_id)
```

### 2. Question Answering System

```python
# 1. Intent Classification
intent = classify_intent(user_question)

# 2. Query Generation
if intent in ["database_query", "rag"]:
    cypher_query = generate_cypher_query(question, schema)
    
# 3. Data Retrieval
records = execute_cypher_query(cypher_query)

# 4. Response Generation
response = generate_response(question, records, conversation_history)
```

### 3. Memory Management

```python
class MemoryManager:
    def __init__(self, max_messages=50):
        self.memory = ConversationBufferMemory()
        self.max_messages = max_messages
        
    def add_message(self, message, is_human=True):
        # Size control
        while len(self.memory.messages) >= self.max_messages:
            self.memory.messages.pop(0)
            
        # Add new message
        if is_human:
            self.memory.add_message(HumanMessage(content=message))
        else:
            self.memory.add_message(AIMessage(content=message))
```

## Data Flow

1. **Bill Upload**:
   ```
   Image → OCR → Text → AI Parser → Structured Data → Neo4j
   ```

2. **Question Processing**:
   ```
   Question → Intent Classification → Query Generation → 
   Data Retrieval → RAG → Response Generation
   ```

3. **Memory Management**:
   ```
   Message → Size Check → Add to Memory → Persist to File
   ```

## API Specifications

### 1. Upload Bill
```http
POST /upload_bill
Content-Type: multipart/form-data

file: <image_file>
```

Response:
```json
{
    "message": "Bill processed successfully!",
    "bill_id": "uuid",
    "data": [
        {
            "item": "string",
            "quantity": "number",
            "price": "number",
            "category": "string"
        }
    ]
}
```

### 2. Ask Question
```http
POST /ask
Content-Type: application/json

{
    "question": "string"
}
```

Response:
```json
{
    "response": "string"
}
```

### 3. Get Memory
```http
GET /memory
```

Response:
```json
{
    "chat_history": ["string"],
    "session_id": "string",
    "message_count": "number"
}
```

## Error Handling

### 1. File Upload Errors
```python
try:
    file = request.files["file"]
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
except Exception as e:
    return jsonify({"error": str(e)}), 500
```

### 2. OCR Errors
```python
try:
    extracted_text = extract_text_easyocr(file_path)
    if not extracted_text:
        raise ValueError("No text extracted from image")
except Exception as e:
    return jsonify({"error": "OCR processing failed"}), 500
```

### 3. Database Errors
```python
try:
    records = execute_cypher_query(query)
except Exception as e:
    return jsonify({"error": "Database query failed"}), 500
```

## Performance Considerations

1. **OCR Processing**:
   - Image preprocessing for better accuracy
   - Caching of processed images
   - Batch processing for multiple bills

2. **Database Operations**:
   - Indexed queries for faster retrieval
   - Connection pooling
   - Query optimization

3. **Memory Management**:
   - Size limits to prevent memory overflow
   - Efficient storage format
   - Regular cleanup of old data

## Security Measures

1. **File Upload**:
   - File type validation
   - Size limits
   - Sanitization of filenames

2. **API Security**:
   - Environment variable protection
   - Input validation
   - Error message sanitization

3. **Database Security**:
   - Credential protection
   - Query parameterization
   - Access control

## Testing

1. **Unit Tests**:
   - OCR accuracy
   - Parser functionality
   - Query generation
   - Memory management

2. **Integration Tests**:
   - End-to-end bill processing
   - Question answering
   - Database operations

3. **Performance Tests**:
   - Response times
   - Memory usage
   - Database query optimization

## Deployment

1. **Requirements**:
   - Python 3.8+
   - Neo4j Database
   - OpenAI API access
   - Sufficient storage for bills

2. **Environment Setup**:
   - Virtual environment
   - Dependencies installation
   - Environment variables configuration

3. **Monitoring**:
   - Error logging
   - Performance metrics
   - Usage statistics 