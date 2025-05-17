# book_agent.py
import os
import json
import asyncio
import argparse
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

def load_config(config_file="config.json"):
    """Load configuration from file"""
    if not os.path.exists(config_file):
        print(f"Configuration file not found: {config_file}")
        exit(1)
    
    with open(config_file, 'r') as f:
        return json.load(f)

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Book Agent")
    parser.add_argument("--provider", "-p", default=None, 
                        help="Provider to use (openai, anthropic, or google)")
    parser.add_argument("--config", "-c", default="config.json", 
                        help="Path to configuration file")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    providers = config.get("providers", {})
    
    # Determine which provider to use
    provider_name = args.provider or config.get("default_provider", "openai")
    if provider_name not in providers:
        print(f"Provider {provider_name} not found in config. Using default.")
        provider_name = "openai"
    
    provider_config = providers.get(provider_name, {})
    api_key = provider_config.get("api_key")
    model = provider_config.get("model")
    
    if not api_key:
        print(f"API key not found for provider: {provider_name}")
        exit(1)
    
    # Set OpenAI API key (needed for Agents SDK)
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Create MCP server connection to our books server
    books_server = MCPServerStdio(
        name="Books Library",
        params={
            "command": "python",
            "args": ["server.py"]
        }
    )
    
    print(f"Starting Books Agent using {provider_name} provider...")
    print("Connecting to MCP server...")
    
    # Use the MCP server in an agent
    async with books_server as server:
        # Create an agent with our MCP server
        agent = Agent(
            name="Books Assistant",
            instructions="""You are a helpful assistant with access to tools for browsing and 
            extracting content from a book library. Your goal is to help users find information
            in books, extract text from specific pages, and navigate book content.
            When a user asks about books or book content, use the appropriate tool to find
            the information.""",
            model=model,
            mcp_servers=[server]
        )
        
        print(f"Agent is ready using {provider_name} with model {model}!")
        print("Type your questions or '/quit' to exit.")
        
        # Interactive chat loop
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() == '/quit':
                break
            
            # Handle provider switching
            if user_input.startswith("/provider "):
                new_provider = user_input.split(" ")[1].strip().lower()
                if new_provider in providers:
                    return await main(["--provider", new_provider])
                else:
                    print(f"Unknown provider: {new_provider}. Available providers: {', '.join(providers.keys())}")
                    continue
            
            print("\nProcessing...")
            
            # Run the agent
            result = await Runner.run(
                agent,
                input=user_input
            )
            
            # Print the response
            print(f"\nAssistant: {result.final_output}")
            if hasattr(result, 'trace_url') and result.trace_url:
                print(f"\nView trace: {result.trace_url}")

if __name__ == "__main__":
    asyncio.run(main())