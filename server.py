import os
import logging
from fastmcp import FastMCP, Context
import pdf_tools

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('books-mcp-server')

# Create the MCP Server
mcp = FastMCP("Books Library")

@mcp.tool()
def list_books() -> list:
    """
    List all available books in the collection with metadata.
    
    Returns:
        A list of books with their metadata including id, title, author (if available),
        and number of pages.
    """
    logger.info("Tool called: list_books()")
    try:
        books = pdf_tools.get_all_books()
        # Simplify the response by removing the full path for security
        for book in books:
            if 'path' in book:
                del book['path']
        
        return books
    except Exception as e:
        logger.error(f"Error in list_books: {str(e)}")
        return [{"error": f"Failed to list books: {str(e)}"}]

@mcp.tool()
def get_table_of_contents(book_id: str) -> list:
    """
    Extract the table of contents from a specific book.
    
    Args:
        book_id: The ID (filename) of the book to extract TOC from
        
    Returns:
        List of TOC entries with title, page number, and nesting level
    """
    logger.info(f"Tool called: get_table_of_contents(book_id='{book_id}')")
    
    # Validate input
    if not book_id:
        return [{"error": "Book ID is required"}]
    
    try:
        # First check if the book exists
        book = pdf_tools.get_book_by_id(book_id)
        if not book:
            return [{"error": f"Book not found: {book_id}"}]
        
        toc = pdf_tools.extract_table_of_contents(book_id)
        return {
            "book_id": book_id,
            "book_title": book.get('title', book_id),
            "toc": toc
        }
    except Exception as e:
        logger.error(f"Error in get_table_of_contents: {str(e)}")
        return {"error": f"Failed to extract table of contents: {str(e)}"}

@mcp.tool()
def extract_pages(book_id: str, pages: str) -> dict:
    """
    Extract text content from specific pages or page ranges of a book.
    
    Args:
        book_id: The ID (filename) of the book
        pages: Page specification like "1-5,8,10-12"
        
    Returns:
        Dictionary with book info and extracted text from specified pages
    """
    logger.info(f"Tool called: extract_pages(book_id='{book_id}', pages='{pages}')")
    
    # Validate inputs
    if not book_id:
        return {"error": "Book ID is required"}
    if not pages:
        return {"error": "Page specification is required"}
    
    try:
        # First check if the book exists
        book = pdf_tools.get_book_by_id(book_id)
        if not book:
            return {"error": f"Book not found: {book_id}"}
        
        result = pdf_tools.extract_pages_text(book_id, pages)
        
        # Add book title for context
        result['book_title'] = book.get('title', book_id)
        return result
    except Exception as e:
        logger.error(f"Error in extract_pages: {str(e)}")
        return {"error": f"Failed to extract pages: {str(e)}"}

@mcp.tool()
def get_book_info(book_id: str) -> dict:
    """
    Get detailed information about a specific book.
    
    Args:
        book_id: The ID (filename) of the book
        
    Returns:
        Dictionary with detailed book metadata
    """
    logger.info(f"Tool called: get_book_info(book_id='{book_id}')")
    
    # Validate input
    if not book_id:
        return {"error": "Book ID is required"}
    
    try:
        book_info = pdf_tools.get_book_info(book_id)
        
        # Remove full path for security
        if 'path' in book_info:
            del book_info['path']
            
        return book_info
    except Exception as e:
        logger.error(f"Error in get_book_info: {str(e)}")
        return {"error": f"Failed to get book info: {str(e)}"}

@mcp.resource("books://list")
def books_list_resource() -> list:
    """Resource providing a list of all available books"""
    books = pdf_tools.get_all_books()
    # Remove full paths for security
    for book in books:
        if 'path' in book:
            del book['path']
    return books

@mcp.resource("books://info/{book_id}")
def book_info_resource(book_id: str) -> dict:
    """Resource providing detailed information about a specific book"""
    book_info = pdf_tools.get_book_info(book_id)
    # Remove full path for security
    if 'path' in book_info:
        del book_info['path']
    return book_info

# Add a health check tool
@mcp.tool()
def ping() -> dict:
    """
    Simple health check to verify the server is running.
    
    Returns:
        Dictionary with status information
    """
    books_count = len(pdf_tools.get_all_books())
    return {
        "status": "ok",
        "books_count": books_count,
        "books_dir": os.path.abspath(pdf_tools.BOOKS_DIR)
    }

# Add/update these tools in server.py

@mcp.tool()
def get_table_of_contents(book_id: str) -> dict:
    """
    Extract the table of contents from a specific book.
    
    Args:
        book_id: The ID or title of the book to extract TOC from
        
    Returns:
        Dictionary with book info and TOC entries
    """
    logger.info(f"Tool called: get_table_of_contents(book_id='{book_id}')")
    
    # Validate input
    if not book_id:
        return {"error": "Book ID is required"}
    
    try:
        # First check if the book exists
        book = pdf_tools.get_book_by_id(book_id)
        if not book:
            return {"error": f"Book not found: {book_id}"}
        
        toc = pdf_tools.extract_table_of_contents(book_id)
        return {
            "book_id": book['id'],  # Return the numeric ID
            "book_title": book.get('title', ''),
            "filename": book.get('filename', ''),
            "toc": toc
        }
    except Exception as e:
        logger.error(f"Error in get_table_of_contents: {str(e)}")
        return {"error": f"Failed to extract table of contents: {str(e)}"}

@mcp.tool()
def extract_pages(book_id: str, pages: str) -> dict:
    """
    Extract text content from specific pages or page ranges of a book.
    
    Args:
        book_id: The ID or title of the book
        pages: Page specification like "1-5,8,10-12"
        
    Returns:
        Dictionary with book info and extracted text from specified pages
    """
    logger.info(f"Tool called: extract_pages(book_id='{book_id}', pages='{pages}')")
    
    # Validate inputs
    if not book_id:
        return {"error": "Book ID is required"}
    if not pages:
        return {"error": "Page specification is required"}
    
    try:
        # First check if the book exists
        book = pdf_tools.get_book_by_id(book_id)
        if not book:
            return {"error": f"Book not found: {book_id}"}
        
        result = pdf_tools.extract_pages_text(book_id, pages)
        
        # Add book information for context
        result['book_id'] = book['id']  # Return the numeric ID
        result['book_title'] = book.get('title', '')
        result['filename'] = book.get('filename', '')
        
        return result
    except Exception as e:
        logger.error(f"Error in extract_pages: {str(e)}")
        return {"error": f"Failed to extract pages: {str(e)}"}

# Create an ASGI app that exposes the MCP server over SSE
app = Starlette(
    routes=[
        Mount('/', app=mcp.sse_app()),
    ]
)

# ... (your existing tool and resource definitions)

if __name__ == "__main__":
    # Ensure the books directory exists
    if not os.path.exists(pdf_tools.BOOKS_DIR):
        os.makedirs(pdf_tools.BOOKS_DIR)
        logger.info(f"Created books directory: {pdf_tools.BOOKS_DIR}")
    
    logger.info(f"Books directory: {os.path.abspath(pdf_tools.BOOKS_DIR)}")
    logger.info(f"Found {len(pdf_tools.get_all_books())} PDF books")
    
    # Print instructions for testing
    print("\n" + "="*80)
    print("Books Library MCP Server")
    print("="*80)
    print(f"Books directory: {os.path.abspath(pdf_tools.BOOKS_DIR)}")
    print("\nTo connect to this server using MCP Inspector:")
    print("1. Run 'npx @modelcontextprotocol/inspector' in another terminal")
    print("2. Select 'STDIO' as the transport type (not SSE)")
    print("3. For command, enter: python server.py")
    print("4. Click 'Connect'")
    print("="*80 + "\n")
    
    # Run the server with STDIO transport
    mcp.run(transport="stdio")