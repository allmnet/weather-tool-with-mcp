# Requirements:
- uv for dependencies
- weatherapi.com key

# Setup:
- copy .example.env to .env and add the weather api key
- create a custom ollama model called llama3.1-tool:8b using the modelfile and llama3.1:8b as a base

# Usage:
```sh
ollama serve
uv run main.py
```
