import pytesseract
from PIL import Image

# Set path to Tesseract OCR (modify based on your OS)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image_path):
    """Extracts raw text from a grocery bill image using Tesseract OCR"""
    img = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(img)
    return extracted_text

# Example Usage
image_path = "grocery_bill.jpg"
raw_text = extract_text_from_image(image_path)
print(raw_text)  # View the raw extracted text

from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

# Define Response Schema for parsing grocery items
response_schemas = [
    ResponseSchema(name="item", description="Name of the grocery item"),
    ResponseSchema(name="quantity", description="Number of items purchased"),
    ResponseSchema(name="price", description="Price of the item"),
]

# Create LangChain Output Parser
parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = parser.get_format_instructions()

# OpenAI API Integration (Optional)
openai_model = ChatOpenAI(model_name="gpt-4", openai_api_key="YOUR_API_KEY")

def parse_grocery_bill(text):
    """Uses LangChain to structure grocery bill text into JSON format"""
    prompt = PromptTemplate(
        template="Extract grocery items, their quantity, and price from the following bill:\n{text}\n\n{format_instructions}",
        input_variables=["text"],
        partial_variables={"format_instructions": format_instructions},
    )

    structured_data = openai_model.predict(prompt.format(text=text))
    return parser.parse(structured_data)

# Example Usage
parsed_data = parse_grocery_bill(raw_text)
print(parsed_data)  # JSON structured data

from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

# Define Response Schema for parsing grocery items
response_schemas = [
    ResponseSchema(name="item", description="Name of the grocery item"),
    ResponseSchema(name="quantity", description="Number of items purchased"),
    ResponseSchema(name="price", description="Price of the item"),
]

# Create LangChain Output Parser
parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = parser.get_format_instructions()

# OpenAI API Integration (Optional)
openai_model = ChatOpenAI(model_name="gpt-4", openai_api_key="YOUR_API_KEY")

def parse_grocery_bill(text):
    """Uses LangChain to structure grocery bill text into JSON format"""
    prompt = PromptTemplate(
        template="Extract grocery items, their quantity, and price from the following bill:\n{text}\n\n{format_instructions}",
        input_variables=["text"],
        partial_variables={"format_instructions": format_instructions},
    )

    structured_data = openai_model.predict(prompt.format(text=text))
    return parser.parse(structured_data)

# Example Usage
parsed_data = parse_grocery_bill(raw_text)
print(parsed_data)  # JSON structured data

from neo4j import GraphDatabase

# Neo4j Connection
URI = "bolt://localhost:7687"  # Update with Neo4j instance
AUTH = ("neo4j", "password")  # Update credentials

class GroceryGraph:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def store_grocery_data(self, user, purchases):
        """Stores grocery purchases in the Neo4j Knowledge Graph"""
        with self.driver.session() as session:
            for purchase in purchases:
                session.run("""
                    MERGE (u:User {name: $user})
                    MERGE (i:Item {name: $item})
                    MERGE (i)-[:BELONGS_TO]->(c:Category {name: $category})
                    MERGE (u)-[:BOUGHT]->(i)
                    SET i.price = $price, i.quantity = $quantity
                """, user=user, item=purchase["item"], category="Unknown", price=purchase["price"], quantity=purchase["quantity"])

# Initialize Neo4j Graph
grocery_graph = GroceryGraph(URI, AUTH)

# Store Data in Neo4j
grocery_graph.store_grocery_data("Sanjana", parsed_data)

def query_total_spent(category):
    """Returns total spending on a category"""
    with grocery_graph.driver.session() as session:
        result = session.run("""
            MATCH (u:User {name: 'Sanjana'})-[:BOUGHT]->(i:Item)-[:BELONGS_TO]->(c:Category {name: $category})
            RETURN SUM(i.price) AS total_spent
        """, category=category)
        
        return result.single()["total_spent"]

# Example Usage
total_dairy_spent = query_total_spent("Dairy")
print(f"Total spent on Dairy: ${total_dairy_spent}")

