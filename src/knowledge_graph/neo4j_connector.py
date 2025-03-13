from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import re

# Load Neo4j credentials
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Simple category mapping for demo (extendable)
CATEGORY_MAPPING = {
    "Milk": "Dairy",
    "Cheese": "Dairy",
    "Bread": "Bakery",
    "Banana": "Fruits",
    "Apple": "Fruits",
    "Garlic": "Spices",
    "Eggs": "Dairy",
    "Chicken": "Meat",
    "Tomato": "Vegetables",
    "Potato": "Vegetables",
    "Strawberries": "Fruits"
}

def extract_numeric_quantity(quantity):
    """Extracts numeric values from quantity (e.g., '1.05 lb' -> 1.05, '2 pcs' -> 2)"""
    match = re.search(r"\d+(\.\d+)?", quantity)  # Match numbers including decimals
    return float(match.group()) if match else 1  # Default to 1 if no number found

class GroceryGraph:
    def __init__(self):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        """Close Neo4j connection."""
        self.driver.close()

    def get_category(self, item_name):
        """Returns category for an item, defaults to 'Other'."""
        for keyword, category in CATEGORY_MAPPING.items():
            if keyword.lower() in item_name.lower():
                return category
        return "Other"
    '''
    def store_grocery_data(self, user, purchases):
        """Stores grocery purchases in Neo4j, assigning correct categories."""
        with self.driver.session() as session:
            for purchase in purchases:
                category = self.get_category(purchase["item"])

                session.run("""
                    MERGE (u:User {name: $user})
                    MERGE (i:Item {name: $item})
                    MERGE (c:Category {name: $category})
                    MERGE (i)-[:BELONGS_TO]->(c)
                    MERGE (u)-[:BOUGHT]->(i)
                    SET i.price = $price, i.quantity = $quantity
                """, user=user, item=purchase["item"], category=category, price=float(purchase["price"]), quantity=int(purchase["quantity"]))
    '''

    

    def store_grocery_data(self, user, purchases,bill_id):
        """Stores grocery purchases in Neo4j with AI-inferred categories."""
        with self.driver.session() as session:
            # ✅ Check if this bill ID already exists
            existing_bill = session.run(
                "MATCH (b:Bill {id: $bill_id}) RETURN b", bill_id=bill_id
            ).single()

            if existing_bill:
                print("✅ Bill already processed, skipping duplicate entry.")
                return

            # ✅ Create a Bill node to track this upload
            session.run(
                "MERGE (b:Bill {id: $bill_id})",
                bill_id=bill_id
            )

            for purchase in purchases:
                category = purchase.get("category", "Uncategorized")
                price = float(purchase.get("price", 0))  # Ensure price is float

                # ✅ Fix: Extract numeric quantity and treat as float
                quantity = extract_numeric_quantity(purchase.get("quantity", "1"))

                print(f"Storing: {purchase['item']} → Category: {category} → Price: {price} → Quantity: {quantity}")

                # ✅ Store quantity as float
                session.run("""
                    MERGE (u:User {name: $user})
                    MERGE (i:Item {name: $item})
                    MERGE (c:Category {name: $category})
                    MERGE (i)-[:BELONGS_TO]->(c)
                    MERGE (u)-[:BOUGHT]->(i)
                    SET i.price = $price, i.quantity = $quantity
                """, user=user, item=purchase["item"], category=category, price=price, quantity=quantity)


# Example Usage
if __name__ == "__main__":
    grocery_graph = GroceryGraph()
    
    sample_data = [
        {"item": "Milk", "quantity": 2, "price": "5.99"},
        {"item": "Banana", "quantity": 6, "price": "1.50"},
        {"item": "Garlic", "quantity": 1, "price": "2.99"},
    ]
    
    grocery_graph.store_grocery_data("Sanjana", sample_data)
    grocery_graph.close()
    print("✅ Data stored successfully in Neo4j!")
