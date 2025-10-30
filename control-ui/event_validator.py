"""
Event Configuration Validator

Validates custom event configurations for the Matomo load generator.
Supports click events and random events with probabilities.
"""
import json
from typing import Dict, List, Any, Optional, Tuple


def validate_event(event: Dict[str, Any], event_type: str = "click") -> Tuple[bool, List[str]]:
    """
    Validate a single event structure.
    
    Args:
        event: Event dictionary to validate
        event_type: Type of event ("click" or "random")
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    required_fields = ['category', 'action', 'name']
    for field in required_fields:
        if field not in event:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(event[field], str) or not event[field].strip():
            errors.append(f"Field '{field}' must be a non-empty string")
    
    # Optional value field
    if 'value' in event:
        if event['value'] is not None:
            if not isinstance(event['value'], (int, float)):
                errors.append(f"Field 'value' must be a number or null")
            elif event['value'] < 0:
                errors.append(f"Field 'value' must be non-negative")
    
    # Check for unexpected fields
    allowed_fields = {'category', 'action', 'name', 'value'}
    unexpected = set(event.keys()) - allowed_fields
    if unexpected:
        errors.append(f"Unexpected fields: {', '.join(unexpected)}")
    
    return len(errors) == 0, errors


def validate_events_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete event configuration.
    
    Args:
        config: Event configuration dictionary
    
    Returns:
        Validation result with status, errors, warnings, and statistics
    """
    errors = []
    warnings = []
    
    # Check root structure
    if not isinstance(config, dict):
        return {
            'valid': False,
            'errors': ['Configuration must be a JSON object'],
            'warnings': [],
            'stats': {}
        }
    
    # Validate probabilities
    if 'click_events_probability' in config:
        prob = config['click_events_probability']
        if not isinstance(prob, (int, float)):
            errors.append("click_events_probability must be a number")
        elif prob < 0 or prob > 1:
            errors.append("click_events_probability must be between 0 and 1")
        elif prob > 0.5:
            warnings.append(f"High click_events_probability ({prob:.2f}). May generate unrealistic traffic.")
    
    if 'random_events_probability' in config:
        prob = config['random_events_probability']
        if not isinstance(prob, (int, float)):
            errors.append("random_events_probability must be a number")
        elif prob < 0 or prob > 1:
            errors.append("random_events_probability must be between 0 and 1")
        elif prob > 0.3:
            warnings.append(f"High random_events_probability ({prob:.2f}). May generate unrealistic traffic.")
    
    # Validate click events
    click_events = config.get('click_events', [])
    if not isinstance(click_events, list):
        errors.append("click_events must be an array")
    else:
        if len(click_events) == 0:
            warnings.append("No click events defined. Visitors won't generate any click events.")
        elif len(click_events) > 100:
            warnings.append(f"{len(click_events)} click events defined. Consider reducing for better performance.")
        
        for idx, event in enumerate(click_events):
            if not isinstance(event, dict):
                errors.append(f"click_events[{idx}] must be an object")
                continue
            
            valid, event_errors = validate_event(event, "click")
            if not valid:
                for err in event_errors:
                    errors.append(f"click_events[{idx}]: {err}")
    
    # Validate random events
    random_events = config.get('random_events', [])
    if not isinstance(random_events, list):
        errors.append("random_events must be an array")
    else:
        if len(random_events) == 0:
            warnings.append("No random events defined. Visitors won't generate any random events.")
        elif len(random_events) > 100:
            warnings.append(f"{len(random_events)} random events defined. Consider reducing for better performance.")
        
        for idx, event in enumerate(random_events):
            if not isinstance(event, dict):
                errors.append(f"random_events[{idx}] must be an object")
                continue
            
            valid, event_errors = validate_event(event, "random")
            if not valid:
                for err in event_errors:
                    errors.append(f"random_events[{idx}]: {err}")
    
    # Calculate statistics
    stats = {
        'click_events_count': len(click_events) if isinstance(click_events, list) else 0,
        'random_events_count': len(random_events) if isinstance(random_events, list) else 0,
        'click_events_probability': config.get('click_events_probability', 0.25),
        'random_events_probability': config.get('random_events_probability', 0.12),
    }
    
    # Category distribution
    if isinstance(click_events, list):
        click_categories = {}
        for event in click_events:
            if isinstance(event, dict) and 'category' in event:
                cat = event['category']
                click_categories[cat] = click_categories.get(cat, 0) + 1
        stats['click_event_categories'] = click_categories
    
    if isinstance(random_events, list):
        random_categories = {}
        for event in random_events:
            if isinstance(event, dict) and 'category' in event:
                cat = event['category']
                random_categories[cat] = random_categories.get(cat, 0) + 1
        stats['random_event_categories'] = random_categories
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'stats': stats
    }


def parse_events_from_loader(loader_content: str) -> Dict[str, Any]:
    """
    Extract event configuration from loader.py content.
    
    Args:
        loader_content: Content of loader.py file
    
    Returns:
        Event configuration dictionary
    """
    # This is a simple parser - in production you'd want something more robust
    import re
    
    config = {
        'click_events': [],
        'random_events': [],
        'click_events_probability': 0.25,
        'random_events_probability': 0.12
    }
    
    # Extract CLICK_EVENTS_PROBABILITY
    match = re.search(r'CLICK_EVENTS_PROBABILITY\s*=\s*float\(os\.environ\.get\([^,]+,\s*"([^"]+)"\)', loader_content)
    if match:
        config['click_events_probability'] = float(match.group(1))
    
    # Extract RANDOM_EVENTS_PROBABILITY
    match = re.search(r'RANDOM_EVENTS_PROBABILITY\s*=\s*float\(os\.environ\.get\([^,]+,\s*"([^"]+)"\)', loader_content)
    if match:
        config['random_events_probability'] = float(match.group(1))
    
    # Extract CLICK_EVENTS array
    match = re.search(r'CLICK_EVENTS\s*=\s*\[(.*?)\]', loader_content, re.DOTALL)
    if match:
        events_str = match.group(1)
        # Parse each event dict
        event_matches = re.finditer(r"\{'category':\s*'([^']+)',\s*'action':\s*'([^']+)',\s*'name':\s*'([^']+)',\s*'value':\s*(None|\d+)\}", events_str)
        for event_match in event_matches:
            value = None if event_match.group(4) == 'None' else int(event_match.group(4))
            config['click_events'].append({
                'category': event_match.group(1),
                'action': event_match.group(2),
                'name': event_match.group(3),
                'value': value
            })
    
    # Extract RANDOM_EVENTS array
    match = re.search(r'RANDOM_EVENTS\s*=\s*\[(.*?)\]', loader_content, re.DOTALL)
    if match:
        events_str = match.group(1)
        # Parse each event dict
        event_matches = re.finditer(r"\{'category':\s*'([^']+)',\s*'action':\s*'([^']+)',\s*'name':\s*'([^']+)',\s*'value':\s*(None|\d+)\}", events_str)
        for event_match in event_matches:
            value = None if event_match.group(4) == 'None' else int(event_match.group(4))
            config['random_events'].append({
                'category': event_match.group(1),
                'action': event_match.group(2),
                'name': event_match.group(3),
                'value': value
            })
    
    return config


def format_events_for_loader(config: Dict[str, Any]) -> str:
    """
    Format event configuration for loader.py file.
    
    Args:
        config: Event configuration dictionary
    
    Returns:
        Python code string for loader.py
    """
    lines = []
    
    # Format CLICK_EVENTS
    lines.append("CLICK_EVENTS = [")
    for event in config.get('click_events', []):
        value_str = 'None' if event.get('value') is None else str(event['value'])
        lines.append(f"    {{'category': '{event['category']}', 'action': '{event['action']}', 'name': '{event['name']}', 'value': {value_str}}},")
    lines.append("]")
    lines.append("")
    
    # Format RANDOM_EVENTS
    lines.append("RANDOM_EVENTS = [")
    for event in config.get('random_events', []):
        value_str = 'None' if event.get('value') is None else str(event['value'])
        lines.append(f"    {{'category': '{event['category']}', 'action': '{event['action']}', 'name': '{event['name']}', 'value': {value_str}}},")
    lines.append("]")
    
    return '\n'.join(lines)
