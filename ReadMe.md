# MCP Books Agent

An AI agent for browsing and extracting content from a book library using the Model Context Protocol (MCP).

## Overview

MCP Books Agent is a Python application that provides an interface between AI models and your PDF book collection. Using the Model Context Protocol (MCP), it enables AI assistants to:

- List and browse your book collection
- Extract and navigate table of contents
- Access specific pages or page ranges from books
- Search for content across your entire library

Built on OpenAI's Agents SDK and Anthropic's Model Context Protocol (MCP), this tool creates a seamless bridge between language models and your personal library.

## Features

- **Book Discovery**: List and filter available books in your collection
- **Content Navigation**: Extract and navigate through table of contents
- **Text Extraction**: Access specific pages or page ranges from any book
- **Provider Flexibility**: Switch between different AI providers (OpenAI, Anthropic, Google)
- **Simple Interface**: Clean, conversational interaction with your book collection

## Prerequisites

- Python 3.10 or higher
- PDF books stored in the `/books` directory
- API keys for at least one of the supported providers:
  - OpenAI
  - Anthropic
  - Google

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd mcp-books
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a configuration file:
   ```bash
   cp dummyconfig.json config.json
   ```
   
4. Edit `config.json` with your API keys:
   ```json
   {
     "providers": {
       "openai": {
         "base_url": "https://api.openai.com/v1",
         "model": "gpt-4o",
         "api_key": "your-openai-key-here"
       },
       "anthropic": {
         "base_url": "https://api.anthropic.com/v1",
         "model": "claude-3-haiku-20240307",
         "api_key": "your-anthropic-key-here"
       },
       "google": {
         "base_url": "https://generativelanguage.googleapis.com/v1",
         "model": "gemini-1.5-pro",
         "api_key": "your-google-key-here"
       }
     },
     "default_provider": "openai"
   }
   ```

5. Add your PDF books to the `books/` directory.

## Usage

### Starting the Agent

Run the agent with your default provider (specified in config.json):

```bash
python book_agent.py
```

Or specify a different provider:

```bash
python book_agent.py --provider anthropic
python book_agent.py --provider google
```

### Using a Custom Configuration File

```bash
python book_agent.py --config my_custom_config.json
```

### Interacting with the Agent

Once started, you'll see a chat interface where you can interact with your book collection. Example commands:

- "List all the books in the library"
- "Show me the table of contents for book 1"
- "Extract pages 10-15 from the book about machine learning"
- "Find mentions of 'neural networks' in all books"

### Switching Providers

You can switch between providers during a session:

```
/provider openai
/provider anthropic
/provider google
```

### Exiting

To exit the application:

```
/quit
```

## Project Structure

```
mcp-books/
├── book_agent.py       # Main agent implementation using OpenAI Agents SDK
├── server.py           # MCP server for book access 
├── pdf_tools.py        # PDF processing utilities
├── config.json         # Configuration with API keys (not in repository)
├── dummyconfig.json    # Template configuration
├── requirements.txt    # Python dependencies
└── books/              # Directory for PDF books
```

## Core Components

### MCP Server (server.py)

The MCP server exposes three key tools:

1. **list_books()**: Returns metadata for all books in the collection
2. **get_table_of_contents(book_id)**: Extracts the TOC from a specific book
3. **extract_pages(book_id, pages)**: Extracts text from specified pages

### PDF Tools (pdf_tools.py)

Provides utilities for processing PDF files:

- Extracting metadata (title, author, etc.)
- Parsing table of contents
- Converting page ranges to page numbers
- Extracting text from specific pages

### Agent (book_agent.py)

Connects the OpenAI Agents SDK to the MCP server, allowing:

- Agent creation with appropriate instructions
- Provider switching
- Interactive chat interface
- Execution of book-related tasks through natural language

## Troubleshooting

### Common Issues

- **MCP server connection errors**: Make sure server.py is in the same directory as book_agent.py
- **PDF extraction issues**: Ensure your PDF files are not encrypted or password protected
- **Provider errors**: Verify your API keys in config.json are correct and active

### Logging

The application logs information to the console. For more detailed logs:

```bash
# Set higher log level
export LOGLEVEL=DEBUG
python book_agent.py
```

## Acknowledgments

- [Anthropic's Model Context Protocol](https://www.anthropic.com/mcp)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [PyPDF Library](https://github.com/py-pdf/pypdf)
- [FastMCP](https://github.com/jlowin/fastmcp)

---