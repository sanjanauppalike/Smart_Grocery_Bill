from src.knowledge_graph.neo4j_connector import GroceryGraph


def query_total_spent(category):
    """Returns total spending on a category."""
    grocery_graph = GroceryGraph()
    
    with grocery_graph.driver.session() as session:
        result = session.run("""
            MATCH (u:User {name: 'Sanjana'})-[:BOUGHT]->(i:Item)-[:BELONGS_TO]->(c:Category)
            WHERE toLower(c.name) = toLower($category)
            RETURN SUM(toFloat(i.price)) AS total_spent
        """, category=category)
        
        # Print the raw query result for debugging
        record = result.single()
        print("Raw Query Result:", record)

        # Extract total spent, ensuring a float conversion
        total_spent = record["total_spent"] if record and record["total_spent"] else 0.0
        grocery_graph.close()
        
        return total_spent

# Example Usage
if __name__ == "__main__":
    total_spent = query_total_spent("Spices")
    print(f"Total spent on Dairy: ${total_spent:.2f}")
