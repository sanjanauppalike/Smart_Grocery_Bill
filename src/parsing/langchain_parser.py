'''from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

# Load OpenAI API Key from .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure API key is set
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API Key is missing. Add it to your .env file.")

# Define expected structure

response_schemas = [
    ResponseSchema(name="item", description="Name of the grocery item"),
    ResponseSchema(name="quantity", description="Quantity of the item"),
    ResponseSchema(name="price", description="Price of the item"),
    ResponseSchema(name="category", description="AI-predicted category of the item (e.g., Dairy, Fruits, Bakery, Snacks, Beverages, etc.)")
]


# Create output parser
parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = parser.get_format_instructions()


# Create output parser
#parser = StructuredOutputParser.from_response_schemas(response_schemas)
#format_instructions = parser.get_format_instructions()

# Initialize OpenAI LLM
openai_model = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY)

def parse_grocery_bill(text):
    """Parses grocery bill text into structured JSON format."""
    prompt = PromptTemplate(
        template="Extract grocery items, their quantity, and price from the following bill:\n{text}\n\n{format_instructions}",
        input_variables=["text"],
        partial_variables={"format_instructions": format_instructions},
    )

    structured_data = openai_model.predict(prompt.format(text=text))
    return parser.parse(structured_data)
'''
'''
import json
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

# Load OpenAI API Key from .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure API key is set
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API Key is missing. Add it to your .env file.")

# Define expected structure

response_schemas = [
    ResponseSchema(name="item", description="Name of the grocery item"),
    ResponseSchema(name="quantity", description="Quantity of the item"),
    ResponseSchema(name="price", description="Price of the item"),
    ResponseSchema(name="category", description="AI-predicted category of the item (e.g., Dairy, Fruits, Bakery, Snacks, Beverages, etc.)")
]


# Create output parser
parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = parser.get_format_instructions()


# Create output parser
#parser = StructuredOutputParser.from_response_schemas(response_schemas)
#format_instructions = parser.get_format_instructions()

# Initialize OpenAI LLM
openai_model = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY)

def sanitize_price(price):
    """Converts price to a float and removes invalid characters."""
    price = re.sub(r"[^\d.]", "", price)  # Remove non-numeric characters except "."
    try:
        return float(price) if price else 0.0  # Convert to float, default to 0.0
    except ValueError:
        return 0.0  # If still invalid, set to 0.0

def parse_grocery_bill(text):
    """Parses grocery bill text into structured JSON format with AI-inferred categories."""
    prompt = PromptTemplate(
        template="""Extract grocery items, their quantity, price, and category from the following bill:
        
        {text}
        
        Assign each item to a logical category (e.g., Dairy, Fruits, Bakery, Beverages, Snacks, Meat, Frozen, Household, Spices, etc.).
        
        Output ONLY in valid JSON format, like this:
        
        [
            {{"item": "Milk", "quantity": "2", "price": "5.99", "category": "Dairy"}},
            {{"item": "Banana", "quantity": "6", "price": "1.50", "category": "Fruits"}},
            {{"item": "Garlic", "quantity": "1", "price": "2.99", "category": "Spices"}}
        ]
        
        {format_instructions}
        """,
        input_variables=["text"],
        partial_variables={"format_instructions": format_instructions},
    )

    try:
        structured_data = openai_model.predict(prompt.format(text=text))

        # ✅ Debug: Print the raw response before parsing
        print("🔹 OpenAI Raw Response:", structured_data)

        # ✅ Ensure OpenAI response is valid JSON
        parsed_json = json.loads(structured_data)

        # ✅ Sanitize price values
        for item in parsed_json:
            item["price"] = sanitize_price(item["price"])

        if isinstance(parsed_json, list) and all(isinstance(entry, dict) for entry in parsed_json):
            return parsed_json  # ✅ Correct format
        else:
            raise ValueError("OpenAI returned an invalid JSON format")

    except json.JSONDecodeError as e:
        print("❌ Failed to parse OpenAI response:", repr(structured_data))  # Debugging step
        raise ValueError(f"Failed to parse OpenAI response: {e}")
'''
import json
import re
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

# Load OpenAI API Key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define expected structured response format
response_schemas = [
    ResponseSchema(name="item", description="Name of the grocery item"),
    ResponseSchema(name="quantity", description="Quantity of the item"),
    ResponseSchema(name="price", description="Price of the item"),
    ResponseSchema(name="category", description="AI-predicted category of the item (e.g., Dairy, Fruits, Snacks, Bakery, etc.)")
]

# Create output parser
parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = parser.get_format_instructions()

# Initialize OpenAI LLM
openai_model = ChatOpenAI(
    model_name="gpt-4",
    openai_api_key=OPENAI_API_KEY,
    temperature=0,  # Ensures deterministic response
)

def sanitize_price(price):
    """Converts price to a float and removes invalid characters."""
    price = re.sub(r"[^\d.]", "", price)  # Remove non-numeric characters except "."
    try:
        return float(price) if price else 0.0  # Convert to float, default to 0.0
    except ValueError:
        return 0.0  # If still invalid, set to 0.0

def parse_grocery_bill(text):
    """Parses grocery bill text into structured JSON format with AI-inferred categories."""
    
    # prompt = PromptTemplate(
    #     template="""Extract grocery items, their quantity, price, and category from the following bill:
        
    #     {text}
        
    #     Assign each item to a logical category (e.g., Dairy, Fruits, Bakery, Beverages, Snacks, Meat, Frozen, Household, Spices, etc.).
        
    #     Output **ONLY** in valid JSON format, structured exactly like this:
        
    #     [
    #         {{"item": "Milk", "quantity": "2", "price": "5.99", "category": "Dairy"}},
    #         {{"item": "Banana", "quantity": "6", "price": "1.50", "category": "Fruits"}},
    #         {{"item": "Garlic", "quantity": "1", "price": "2.99", "category": "Spices"}}
    #     ]
        
    #     {format_instructions}
    #     """,
    #     input_variables=["text"],
    #     partial_variables={"format_instructions": format_instructions},
    # )
    prompt = PromptTemplate(
        template="""Extract grocery items, their quantity, price, and category from the following bill:
        
        {text}
        
        - Assign each item to a logical category (e.g., Dairy, Fruits, Bakery, Beverages, Snacks, Meat, Frozen, Household, Spices, etc.).
        - Always use the "You Paid" price instead of the listed price when available.
        - Ensure all numbers are correctly formatted as floating-point values.
        - If quantity is missing, assume it is 1.

        Return **only** valid JSON output structured like this:
        
        [
            {{"item": "Milk", "quantity": "2", "price": "5.99", "category": "Dairy"}},
            {{"item": "Banana", "quantity": "6", "price": "1.50", "category": "Fruits"}},
            {{"item": "Garlic", "quantity": "1", "price": "2.99", "category": "Spices"}}
        ]
        
        {format_instructions}
        """,
        input_variables=["text"],
        partial_variables={"format_instructions": format_instructions},
    )

    try:
        structured_data = openai_model.predict(prompt.format(text=text))

        # ✅ Debug: Print the raw OpenAI response before parsing
        print("🔹 OpenAI Raw Response:", structured_data)

        # ✅ Remove Markdown-like triple backticks and extra formatting
        structured_data = structured_data.strip("```json").strip("```").strip()

        # ✅ Step 2: Remove Non-JSON Explanations (if OpenAI includes additional text)
        json_match = re.search(r"\[\s*\{.*\}\s*\]", structured_data, re.DOTALL)
        if json_match:
            structured_data = json_match.group(0)  # Extract only JSON part

        # ✅ Ensure OpenAI response is valid JSON
        parsed_json = json.loads(structured_data)

        # ✅ Sanitize price values
        for item in parsed_json:
            item["price"] = sanitize_price(item["price"])

        if isinstance(parsed_json, list) and all(isinstance(entry, dict) for entry in parsed_json):
            return parsed_json  # ✅ Correct format
        else:
            raise ValueError("OpenAI returned an invalid JSON format")

    except json.JSONDecodeError as e:
        print("❌ Failed to parse OpenAI response:", repr(structured_data))  # Debugging step
        raise ValueError(f"Failed to parse OpenAI response: {e}")
