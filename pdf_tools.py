import os
import re
from typing import Dict, List, Optional, Tuple, Union
from pypdf import PdfReader



# Define the directory where books are stored
BOOKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "books")

# In-memory mapping of numeric IDs to filenames
_id_to_filename = {}
_filename_to_id = {}
_next_id = 1



def _load_book_mappings():
    """Initialize the ID mappings for all books"""
    global _next_id, _id_to_filename, _filename_to_id
    
    # Reset mappings
    _id_to_filename = {}
    _filename_to_id = {}
    _next_id = 1
    
    # Ensure the books directory exists
    if not os.path.exists(BOOKS_DIR):
        os.makedirs(BOOKS_DIR)
        return
    
    # Create mappings for all PDF files
    for filename in sorted(os.listdir(BOOKS_DIR)):
        if filename.lower().endswith('.pdf'):
            _id_to_filename[str(_next_id)] = filename
            _filename_to_id[filename] = str(_next_id)
            _next_id += 1

def get_all_books() -> List[Dict[str, Union[str, int]]]:
    """
    List all PDF books in the books directory with metadata.
    
    Returns:
        List of dictionaries containing book information:
        - id: Numeric identifier
        - filename: Original filename
        - title: Extracted title (or filename if extraction fails)
        - size: File size in bytes
        - pages: Total number of pages
    """
    # Ensure mappings are initialized
    _load_book_mappings()
    
    books = []
    
    for book_id, filename in _id_to_filename.items():
        file_path = os.path.join(BOOKS_DIR, filename)
        book_info = {
            'id': book_id,
            'filename': filename,
            'path': file_path,
            'size': os.path.getsize(file_path),
        }
        
        # Extract additional metadata from PDF
        try:
            reader = PdfReader(file_path)
            book_info['pages'] = len(reader.pages)
            
            # Try to extract title from metadata
            if reader.metadata and reader.metadata.title:
                book_info['title'] = reader.metadata.title
            else:
                # Use filename without extension as fallback title
                book_info['title'] = os.path.splitext(filename)[0]
                
            # Try to extract author from metadata
            if reader.metadata and reader.metadata.author:
                book_info['author'] = reader.metadata.author
        except Exception as e:
            # If PDF parsing fails, use basic information
            book_info['title'] = os.path.splitext(filename)[0]
            book_info['error'] = str(e)
        
        books.append(book_info)
    
    return books

def get_book_by_id(book_id: str) -> Optional[Dict[str, Union[str, int]]]:
    """
    Get information about a specific book by its ID.
    
    Args:
        book_id: The numeric ID or filename of the book
        
    Returns:
        Dictionary with book information or None if not found
    """
    # Ensure mappings are initialized
    _load_book_mappings()
    
    # Check if the ID is a numeric ID
    if book_id in _id_to_filename:
        filename = _id_to_filename[book_id]
    elif book_id in _filename_to_id:
        # It's a filename itself
        filename = book_id
    else:
        # Try to find by title (partial match)
        all_books = get_all_books()
        for book in all_books:
            if book_id.lower() in book.get('title', '').lower():
                return book
        return None
    
    file_path = os.path.join(BOOKS_DIR, filename)
    if not os.path.exists(file_path):
        return None
    
    book_info = {
        'id': _filename_to_id.get(filename, 'unknown'),
        'filename': filename,
        'path': file_path,
        'size': os.path.getsize(file_path),
    }
    
    # Extract additional metadata
    try:
        reader = PdfReader(file_path)
        book_info['pages'] = len(reader.pages)
        
        if reader.metadata and reader.metadata.title:
            book_info['title'] = reader.metadata.title
        else:
            book_info['title'] = os.path.splitext(filename)[0]
            
        if reader.metadata and reader.metadata.author:
            book_info['author'] = reader.metadata.author
    except Exception as e:
        book_info['title'] = os.path.splitext(filename)[0]
        book_info['error'] = str(e)
    
    return book_info

# Update the remaining functions to work with the new ID system

def extract_table_of_contents(book_id: str) -> List[Dict[str, Union[str, int]]]:
    """Extract the table of contents from a PDF book."""
    book = get_book_by_id(book_id)
    if not book:
        return []
    
    toc = []
    try:
        reader = PdfReader(book['path'])
        
        # In newer versions of PyPDF, the outline might be a method or an attribute
        # Try different approaches to access the outline
        outline = None
        
        # Method 1: Try to access outline as an attribute
        if hasattr(reader, 'outline') and reader.outline:
            outline = reader.outline
        
        # Method 2: Try to access outlines as a property or method
        elif hasattr(reader, 'outlines'):
            if callable(reader.outlines):
                outline = reader.outlines()
            else:
                outline = reader.outlines
        
        # Process outlines if available
        if outline:
            def process_outline_item(item, level=0):
                # Check if item is a list or sequence
                if isinstance(item, (list, tuple)):
                    items = []
                    for subitem in item:
                        items.extend(process_outline_item(subitem, level))
                    return items
                
                # Handle dictionary-like objects (typical for PDF outline items)
                elif hasattr(item, 'keys') or isinstance(item, dict):
                    # Extract title and destination
                    entry = {
                        'title': item.get('/Title', 'Unnamed Section'),
                        'level': level
                    }
                    
                    # Try to get the page number
                    try:
                        if '/Dest' in item and item['/Dest']:
                            page_ref = None
                            if isinstance(item['/Dest'], list) and len(item['/Dest']) > 0:
                                page_ref = item['/Dest'][0]
                            
                            # Try to get the page number
                            if page_ref:
                                for i, page in enumerate(reader.pages):
                                    if page.indirect_reference == page_ref:
                                        entry['page'] = i + 1  # 1-based page numbers
                                        break
                    except:
                        pass
                    
                    # Get children if any
                    children = []
                    if '/Count' in item and item['/Count'] > 0 and '/First' in item:
                        child = item['/First']
                        while child:
                            children.extend(process_outline_item(child, level + 1))
                            if '/Next' in child:
                                child = child['/Next']
                            else:
                                break
                    
                    return [entry] + children
                
                # Handle other types of outline items
                else:
                    try:
                        title = getattr(item, 'title', str(item))
                        entry = {
                            'title': title,
                            'level': level
                        }
                        
                        # Try to get page number
                        try:
                            page_num = reader.get_destination_page_number(item)
                            if page_num is not None:
                                entry['page'] = page_num + 1  # 1-based page numbers
                        except:
                            pass
                        
                        # Get children if available
                        children = []
                        if hasattr(item, 'children') and item.children:
                            for child in item.children:
                                children.extend(process_outline_item(child, level + 1))
                        
                        return [entry] + children
                    except:
                        # Can't process this item
                        return []
            
            # Try to process the outline
            try:
                toc = process_outline_item(outline)
            except Exception as e:
                toc = [{'error': f"Error processing outline: {str(e)}"}]
        
        # If no TOC found or processing failed, generate a simple one
        if not toc or (len(toc) == 1 and 'error' in toc[0]):
            # Create a simple chapter-based TOC
            # Check for possible chapter headings in the first few pages
            chapter_toc = []
            
            # Try to scan first 20 pages for chapter headings
            num_pages_to_scan = min(20, len(reader.pages))
            
            for i in range(num_pages_to_scan):
                text = reader.pages[i].extract_text()
                
                # Look for patterns like "Chapter 1", "CHAPTER ONE", etc.
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if (line.lower().startswith('chapter') or 
                            line.lower().startswith('section') or
                            (len(line) < 50 and line.isupper())):  # Potential heading
                            chapter_toc.append({
                                'title': line,
                                'page': i + 1,
                                'level': 0
                            })
            
            if chapter_toc:
                toc = chapter_toc
            else:
                # Fallback to a minimal TOC
                toc = [{'title': 'Document Start', 'page': 1, 'level': 0}]
                
                # Add approximate chapter markers if it's a longer document
                if len(reader.pages) > 10:
                    page_interval = max(10, len(reader.pages) // 5)
                    for i in range(page_interval, len(reader.pages), page_interval):
                        toc.append({
                            'title': f'Section starting at page {i+1}',
                            'page': i + 1,
                            'level': 0
                        })
                
    except Exception as e:
        toc = [{'error': str(e)}]
    
    return toc

def extract_pages_text(book_id: str, page_range_str: str) -> Dict[str, Union[str, List[Dict[int, str]]]]:
    """Extract text content from specific pages or page ranges of a PDF."""
    result = {
        'book_id': book_id,
        'pages': []
    }
    
    book = get_book_by_id(book_id)
    if not book:
        result['error'] = f"Book not found: {book_id}"
        return result
    
    # Update the result with the book's numeric ID and title
    result['book_id'] = book['id']
    result['book_title'] = book.get('title', '')
    
    # Rest of the function remains the same
    try:
        reader = PdfReader(book['path'])
        max_pages = len(reader.pages)
        
        # Parse the page ranges
        page_numbers = parse_page_ranges(page_range_str, max_pages)
        
        if not page_numbers:
            result['error'] = f"No valid pages specified in range: {page_range_str}"
            return result
        
        # Extract text from each specified page
        for page_num in page_numbers:
            # Convert from 1-based to 0-based indexing
            pdf_page = reader.pages[page_num - 1]
            text = pdf_page.extract_text()
            
            result['pages'].append({
                'page_number': page_num,
                'text': text
            })
            
    except Exception as e:
        result['error'] = f"Error extracting pages: {str(e)}"
    
    return result

# The parse_page_ranges function remains unchanged
def parse_page_ranges(page_range_str: str, max_pages: int) -> List[int]:
    """Parse a page range string into a list of page numbers."""
    if not page_range_str:
        return []
    
    pages = []
    ranges = page_range_str.split(',')
    
    for r in ranges:
        r = r.strip()
        if not r:
            continue
            
        # Check if it's a range (e.g., "1-5")
        if '-' in r:
            try:
                start, end = map(int, r.split('-', 1))
                # Ensure start <= end and both are within bounds
                start = max(1, min(start, max_pages))
                end = max(start, min(end, max_pages))
                pages.extend(range(start, end + 1))
            except ValueError:
                # Skip invalid ranges
                continue
        else:
            # Single page number
            try:
                page = int(r)
                if 1 <= page <= max_pages:
                    pages.append(page)
            except ValueError:
                # Skip invalid page numbers
                continue
    
    # Remove duplicates and sort
    return sorted(set(pages))

def get_book_info(book_id: str) -> Dict[str, Union[str, int]]:
    """Get detailed information about a specific book."""
    book = get_book_by_id(book_id)
    if not book:
        return {'error': f"Book not found: {book_id}"}
    
    # Additional metadata extraction logic remains the same
    try:
        reader = PdfReader(book['path'])
        
        # Extract more metadata if available
        if reader.metadata:
            for key in ['author', 'creator', 'producer', 'subject', 'title']:
                if hasattr(reader.metadata, key) and getattr(reader.metadata, key):
                    book[key] = getattr(reader.metadata, key)
                    
        # Add page count
        book['page_count'] = len(reader.pages)
        
        # Add creation and modification dates if available
        if hasattr(reader.metadata, 'creation_date') and reader.metadata.creation_date:
            book['creation_date'] = str(reader.metadata.creation_date)
            
        if hasattr(reader.metadata, 'modification_date') and reader.metadata.modification_date:
            book['modification_date'] = str(reader.metadata.modification_date)
            
    except Exception as e:
        book['error'] = f"Error reading PDF metadata: {str(e)}"
    
    return book

# Initialize the ID mappings when the module is loaded
_load_book_mappings()