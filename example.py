#!/usr/bin/env python3
"""
Example script demonstrating FastData usage

Requirements:
- Install dependencies: pip install -e .
- Set up API credentials for your chosen provider (OpenAI, Anthropic, etc.)
"""

from pydantic import BaseModel
from fastdata.core import FastData

def main():
    # Initialize FastData
    fd = FastData()
    
    # Define the data schema
    class Book(BaseModel):
        name: str
        author: str
    
    # Generate data
    print("Generating book recommendations...")
    results = fd.generate(
        prompt_template="Recommend a {genre} book", 
        inputs=[
            {"genre": "financial success"}, 
            {"genre": "productivity"}
        ],
        schema=Book,
        sp="You are a librarian"
    )
    
    # Display results
    print("\nGenerated recommendations:")
    for i, result in enumerate(results, 1):
        if result:
            print(f"{i}. {result}")
        else:
            print(f"{i}. Failed to generate recommendation")

if __name__ == "__main__":
    main()