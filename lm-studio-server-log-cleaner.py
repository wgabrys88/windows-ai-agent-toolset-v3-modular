#!/usr/bin/env python3
import sys
import json
import re

def truncate_base64_images(json_obj):
    """
    Recursively find and truncate base64 image data in JSON object.
    """
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if key == "url" and isinstance(value, str) and value.startswith("data:image/"):
                # Keep prefix and add ellipsis
                prefix = value[:50] if len(value) > 50 else value
                json_obj[key] = prefix + "...[truncated]"
            else:
                truncate_base64_images(value)
    elif isinstance(json_obj, list):
        for item in json_obj:
            truncate_base64_images(item)
    
    return json_obj


def extract_json_from_position(lines, start_idx):
    """
    Extract a complete JSON object starting from start_idx.
    Returns (json_object, next_line_index) or (None, next_line_index) if parsing fails.
    """
    json_lines = []
    brace_count = 0
    in_string = False
    escape_next = False
    i = start_idx
    
    while i < len(lines):
        line = lines[i]
        
        for char in line:
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
        
        json_lines.append(line)
        
        # If we've closed all braces and we had at least one opening brace
        if brace_count == 0 and len(json_lines) > 0:
            break
        
        i += 1
    
    # Try to parse the JSON
    try:
        json_str = '\n'.join(json_lines)
        json_obj = json.loads(json_str)
        return json_obj, i + 1
    except json.JSONDecodeError as e:
        return None, i + 1

def clean_log(input_filename):
    """
    Cleans LM Studio log file to extract only JSON message exchanges.
    """
    
    with open(input_filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cleaned_lines = []
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for request with JSON starting on the same line
        request_match = re.search(r'Received request: POST to /v1/chat/completions with body (\{.*)$', line)
        if request_match:
            timestamp_match = re.match(r'\[([^\]]+)\]', line)
            timestamp = timestamp_match.group(1) if timestamp_match else 'TIMESTAMP'
            
            cleaned_lines.append(f"\n{'='*80}")
            cleaned_lines.append(f"[{timestamp}] REQUEST TO MODEL:")
            cleaned_lines.append('='*80)
            
            # Start extracting JSON from the opening brace on this line
            # First, find where the { starts
            brace_pos = line.index('{')
            first_line = line[brace_pos:]
            
            # Create a temporary lines array starting with the JSON part
            temp_lines = [first_line] + lines[i+1:]
            json_obj, offset = extract_json_from_position(temp_lines, 0)
            
            if json_obj:
                json_obj = truncate_base64_images(json_obj)  # Add this line
                cleaned_lines.append(json.dumps(json_obj, indent=2))

                i += offset
            else:
                cleaned_lines.append("[ERROR: Could not parse JSON]")
                i += 1
            
            continue
        
        # Check for response with JSON starting on the same line
        response_match = re.search(r'Generated prediction: (\{.*)$', line)
        if response_match:
            timestamp_match = re.match(r'\[([^\]]+)\]', line)
            timestamp = timestamp_match.group(1) if timestamp_match else 'TIMESTAMP'
            
            cleaned_lines.append(f"\n{'='*80}")
            cleaned_lines.append(f"[{timestamp}] RESPONSE FROM MODEL:")
            cleaned_lines.append('='*80)
            
            # Start extracting JSON from the opening brace on this line
            brace_pos = line.index('{')
            first_line = line[brace_pos:]
            
            # Create a temporary lines array starting with the JSON part
            temp_lines = [first_line] + lines[i+1:]
            json_obj, offset = extract_json_from_position(temp_lines, 0)
            
            if json_obj:
                json_obj = truncate_base64_images(json_obj)  # Add this line
                cleaned_lines.append(json.dumps(json_obj, indent=2))

                i += offset
            else:
                cleaned_lines.append("[ERROR: Could not parse JSON]")
                i += 1
            
            continue
        
        i += 1
    
    # Generate output filename
    output_filename = input_filename.rsplit('.', 1)[0] + '_clean'
    if '.' in input_filename:
        output_filename += '.' + input_filename.rsplit('.', 1)[1]
    else:
        output_filename += '.txt'
    
    # Write cleaned content
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))
    
    request_count = len([l for l in cleaned_lines if 'REQUEST TO MODEL' in l])
    response_count = len([l for l in cleaned_lines if 'RESPONSE FROM MODEL' in l])
    print(f"Cleaned log written to: {output_filename}")
    print(f"Extracted {request_count} requests and {response_count} responses")
    return output_filename

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <log_filename>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        clean_log(input_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
