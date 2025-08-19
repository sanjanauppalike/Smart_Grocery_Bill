# Grocery Bill Analyzer With LLM & RAG

A sophisticated application that leverages advanced NLP, OCR, and AI technologies to transform grocery bills into actionable insights. The system uses a combination of cutting-edge technologies to provide intelligent analysis of spending patterns and natural conversation about grocery purchases.

## Technology Stack

### Core Technologies
- **OCR (Optical Character Recognition)**: EasyOCR for accurate text extraction from bill images
- **Natural Language Processing**: 
  - GPT-4 for advanced text understanding and generation
  - LangChain for structured data extraction and processing
  - RAG (Retrieval Augmented Generation) for context-aware responses
- **Graph Database**: Neo4j for storing and analyzing complex relationships between items, categories, and purchases
- **Frontend**: Streamlit for an intuitive, responsive user interface
- **Backend**: Flask for robust API endpoints and business logic

### Key Features

#### 1. Intelligent Bill Processing
-  Advanced OCR with EasyOCR for accurate text extraction
-  AI-powered item categorization and price extraction
-  Automatic spending pattern analysis
-  Smart data validation and error correction

#### 2. Natural Language Understanding
-  Context-aware question answering
-  Session-based conversation memory
-  Intent classification for query routing
-  Dynamic response generation using RAG

#### 3. Data Analysis
- Spending analytics by category
- Price and quantity tracking
- Purchase frequency analysis
- Budget insights and trends

#### 4. User Experience
- Clean, intuitive interface
- Real-time processing
- Conversation history
- Visual data representation

## Quick Start

1. **Install Dependencies**:
```bash
pip install -r requirement.txt
```

2. **Set Up Environment**:
Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_api_key
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

3. **Run the Application**:
```bash
# Start the backend
python src/api/grocery_api.py

# Start the frontend
streamlit run src/ui/app.py
```

4. **Open in Browser**:
```
http://localhost:8501
```

## How to Use

1. **Upload Your Bill**:
   - Click "Upload Your Grocery Bill Image"
   - Select a clear image of your grocery bill
   - Click "Process Bill"

2. **View Your Data**:
   - See extracted items and prices
   - View spending by category
   - Check total spending

3. **Ask Questions**:
   - Type questions in the chat box
   - Get instant insights about your spending
   - Examples:
     - "What's my most expensive item?"
     - "How much did I spend on produce?"
     - "What items do I buy most often?"

4. **Manage History**:
   - View past conversations
   - Clear history when needed
   - Track spending over time

## System Architecture

The application follows a modern microservices architecture:

```
Frontend (Streamlit) → Backend (Flask) → Services
                                    ↓
                            Database (Neo4j)
```

### Key Components:
1. **OCR Service**: Handles image processing and text extraction
2. **NLP Service**: Manages text understanding and response generation
3. **Graph Service**: Handles data storage and relationship queries
4. **Memory Service**: Manages conversation context and history

For detailed technical documentation, see [TECHNICAL.md](TECHNICAL.md)

## Troubleshooting

Common issues and solutions:
1. **Upload fails**:
   - Ensure image is clear and well-lit
   - Check file size (max 10MB)
   - Supported formats: PNG, JPG, JPEG

2. **Processing errors**:
   - Verify Neo4j is running
   - Check API keys in .env
   - Ensure sufficient disk space

3. **Chat not working**:
   - Verify OpenAI API key
   - Try refreshing the page

