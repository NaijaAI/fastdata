# fastdata

A minimal library for generating synthetic data using LLMs (Large Language Models).

## Overview

`fastdata` provides a simple interface for generating structured synthetic data using various LLM providers. It supports rate limiting, concurrent processing, and direct integration with Hugging Face Hub.

## Quick Start

First, define your data schema using Pydantic:

```python
from pydantic import BaseModel
from fastdata.core import FastData

class Book(BaseModel):
    name: str
    author: str

# Initialize FastData (supports OpenAI, Anthropic, etc.)
fd = FastData(model="gpt-4.1-nano", provider="openai")

# Generate data
results = fd.generate(
    prompt_template="Recommend a {genre} book", 
    inputs=[
        {"genre": "financial success"}, 
        {"genre": "productivity"}
    ],
    schema=Book,
    sp="You are a librarian"
)

print(results)
```

## Features

- **Multiple LLM Providers**: Supports OpenAI, Anthropic, and other providers via [Mirascope](https://github.com/mirascope/mirascope)
- **Structured Output**: Uses Pydantic models for type-safe data generation
- **Rate Limiting**: Built-in rate limiting to respect API limits
- **Concurrent Processing**: Parallel API calls for faster generation
- **Hugging Face Integration**: Direct upload to Hugging Face Hub datasets
- **Progress Tracking**: Built-in progress bars with tqdm

## Installation

Install in development mode:

```sh
pip install -e .
```

## Usage Examples

### Basic Generation

See `example.py` for a complete working example:

```sh
python example.py
```

### Generate to Hugging Face Hub

```python
from fastdata.core import FastData
from pydantic import BaseModel

class Recipe(BaseModel):
    name: str
    ingredients: list[str]
    instructions: str

fd = FastData()
repo_id, data = fd.generate_to_hf(
    prompt_template="Create a {cuisine} recipe",
    inputs=[{"cuisine": "Italian"}, {"cuisine": "Mexican"}],
    schema=Recipe,
    repo_id="username/recipe-dataset"
)
```

## API Configuration

Set up your API credentials:

```python
# OpenAI
fd = FastData(model="gpt-4.1-nano", provider="openai")

# Anthropic
fd = FastData(model="claude-3-haiku-20240307", provider="anthropic")
```

## Attribution

This project is based on the original [FastData](https://github.com/AnswerDotAI/fastdata) by AnswerDotAI.
