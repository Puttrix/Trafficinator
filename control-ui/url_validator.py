"""
URL validation and management for Trafficinator

Validates and parses URL files for the load generator.
"""
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse
import re


class URLValidationError(Exception):
    """Raised when URL validation fails"""
    pass


def validate_url_line(line: str, line_number: int) -> Tuple[str, Optional[str]]:
    """
    Validate a single URL line.
    
    Format: URL [TAB] Optional Title
    Example: https://example.test/path    Page Title
    
    Args:
        line: Line to validate
        line_number: Line number for error reporting
    
    Returns:
        Tuple of (url, title)
    
    Raises:
        URLValidationError: If line is invalid
    """
    line = line.strip()
    
    # Skip empty lines and comments
    if not line or line.startswith('#'):
        return None, None
    
    # Split by tab or multiple spaces
    parts = re.split(r'\t+|\s{2,}', line, maxsplit=1)
    url = parts[0].strip()
    title = parts[1].strip() if len(parts) > 1 else None
    
    # Validate URL format
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            raise URLValidationError(
                f"Line {line_number}: URL must include scheme (http:// or https://): {url}"
            )
        if parsed.scheme not in ['http', 'https']:
            raise URLValidationError(
                f"Line {line_number}: URL scheme must be http or https: {url}"
            )
        if not parsed.netloc:
            raise URLValidationError(
                f"Line {line_number}: URL must include domain: {url}"
            )
    except Exception as e:
        if isinstance(e, URLValidationError):
            raise
        raise URLValidationError(f"Line {line_number}: Invalid URL format: {url}")
    
    return url, title


def validate_urls(content: str) -> Dict[str, any]:
    """
    Validate URLs content.
    
    Args:
        content: Raw URL file content
    
    Returns:
        Dict with validation results:
        {
            'valid': bool,
            'errors': List[str],
            'warnings': List[str],
            'url_count': int,
            'urls': List[Dict] - parsed URLs with metadata
        }
    """
    lines = content.split('\n')
    errors = []
    warnings = []
    urls = []
    
    for i, line in enumerate(lines, start=1):
        try:
            url, title = validate_url_line(line, i)
            if url:  # Skip empty/comment lines
                urls.append({
                    'url': url,
                    'title': title,
                    'line': i
                })
        except URLValidationError as e:
            errors.append(str(e))
    
    # Warnings
    if len(urls) < 10:
        warnings.append(f"Only {len(urls)} URLs found. Recommend at least 100 for diverse traffic.")
    elif len(urls) < 100:
        warnings.append(f"Only {len(urls)} URLs found. Consider adding more for better variety.")
    
    if len(urls) > 50000:
        warnings.append(f"{len(urls)} URLs may impact memory usage. Consider reducing if container runs out of memory.")
    
    # Check for duplicate URLs
    url_set = set()
    duplicates = []
    for url_data in urls:
        if url_data['url'] in url_set:
            duplicates.append(url_data['url'])
        url_set.add(url_data['url'])
    
    if duplicates:
        warnings.append(f"Found {len(duplicates)} duplicate URLs (first few): {', '.join(duplicates[:5])}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'url_count': len(urls),
        'urls': urls
    }


def parse_url_structure(urls: List[Dict]) -> Dict[str, any]:
    """
    Parse URL structure to extract categories, subcategories, and hierarchy.
    
    Args:
        urls: List of URL dicts with 'url' and 'title' keys
    
    Returns:
        Dict with structure information:
        {
            'total_urls': int,
            'unique_domains': int,
            'categories': Dict[category, count],
            'hierarchy': Dict - nested structure
        }
    """
    domains = set()
    categories = {}
    hierarchy = {}
    
    for url_data in urls:
        url = url_data['url']
        parsed = urlparse(url)
        domains.add(parsed.netloc)
        
        # Parse path structure
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if path_parts:
            # First part is category
            category = path_parts[0]
            categories[category] = categories.get(category, 0) + 1
            
            # Build hierarchy
            if category not in hierarchy:
                hierarchy[category] = {'subcategories': {}, 'pages': []}
            
            if len(path_parts) > 1:
                subcategory = path_parts[1]
                if subcategory not in hierarchy[category]['subcategories']:
                    hierarchy[category]['subcategories'][subcategory] = []
                
                # Store page info
                page_id = '/'.join(path_parts[2:]) if len(path_parts) > 2 else subcategory
                hierarchy[category]['subcategories'][subcategory].append({
                    'url': url,
                    'title': url_data.get('title'),
                    'page_id': page_id
                })
            else:
                hierarchy[category]['pages'].append({
                    'url': url,
                    'title': url_data.get('title')
                })
    
    # Calculate statistics
    total_categories = len(categories)
    total_subcategories = sum(
        len(cat_data['subcategories']) 
        for cat_data in hierarchy.values()
    )
    
    return {
        'total_urls': len(urls),
        'unique_domains': len(domains),
        'total_categories': total_categories,
        'total_subcategories': total_subcategories,
        'categories': categories,
        'hierarchy': hierarchy
    }


def format_urls_for_file(urls: List[Dict]) -> str:
    """
    Format URLs list into file content.
    
    Args:
        urls: List of URL dicts with 'url' and optional 'title' keys
    
    Returns:
        Formatted content string
    """
    lines = []
    for url_data in urls:
        url = url_data['url']
        title = url_data.get('title')
        if title:
            lines.append(f"{url}\t{title}")
        else:
            lines.append(url)
    return '\n'.join(lines)
