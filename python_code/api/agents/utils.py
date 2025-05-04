import json
import re
import time
import logging
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("utils")

def get_chatbot_response(client, model_name, messages, temperature=0):
    input_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    # Estimate input tokens to set max_response_tokens dynamically
    input_text = " ".join(msg["content"] for msg in messages)
    estimated_input_tokens = int(len(input_text.split()) * 1.3) # Simple estimate

    #max_total_tokens = 8192 # Model limit llama-3-8B
    max_total_tokens = 128000 # Model limit llama-3.1-8B
    max_response_tokens = max_total_tokens - estimated_input_tokens
    # Clamp response tokens to a reasonable range, increasing upper limit
    # Old: max(512, min(max_response_tokens, 2048))
    max_response_tokens = max(512, min(max_response_tokens, 8192)) # Increased upper clamp to 8192
    logger.debug(f"Calculated max_response_tokens: {max_response_tokens}") # Add log

    # Retry mechanism
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.1-8B-Instruct",
                messages=input_messages,
                temperature=temperature,
                top_p=0.8,
                max_tokens=max_response_tokens,
                timeout=30,
            )
            logger.info(f"Raw API Response (Attempt {attempt + 1}): {response}") # Log the raw response
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2 # Exponential backoff
            else:
                logger.error(f"API call failed after {max_retries} attempts.")
                # Return default error structure
                return '{"decision": "allowed", "message": "Sorry, I encountered a temporary issue. Please try again.", "chain_of_thought": "Error in API call after retries"}'


def get_embedding(embedding_client, model_name, text_input):
    output = embedding_client.embeddings.create(input=text_input, model=model_name)
    
    return [embedding_object.embedding for embedding_object in output.data]

# Pre-compiled regex for extracting JSON objects
JSON_PATTERN = re.compile(r'({[\s\S]*})')

@lru_cache(maxsize=100) # Cache validation results
def _validate_json_string(json_string):
    """Helper function to validate JSON string and cache results"""
    try:
        return json.loads(json_string), True
    except json.JSONDecodeError:
        return None, False

def double_check_json_output(client, model_name, json_string):
    """Validates if a string is valid JSON, attempts regex extraction if not."""
    # Strip leading/trailing whitespace before any validation
    json_string = json_string.strip()
    logger.debug(f"Checking JSON (stripped): {json_string}")
    _, is_valid = _validate_json_string(json_string)
    if is_valid:
        # Already valid JSON
        logger.debug("Input is valid JSON.")
        return json_string # Return original string as it's valid

    if not json_string or json_string.strip() == "":
        logger.warning("Input string is empty. Returning default JSON.")
        return '{"decision": "allowed", "message": "", "chain_of_thought": "Empty input string"}'

    # Attempt to extract JSON using regex if direct validation failed
    simplified_json = json_string.strip()
    json_match = JSON_PATTERN.search(simplified_json)
    if json_match:
        extracted_json = json_match.group(0)
        _, is_valid_extracted = _validate_json_string(extracted_json)
        if is_valid_extracted:
            logger.debug("Extracted valid JSON with regex.")
            return extracted_json # Return the extracted valid JSON string

    # If direct validation and regex extraction failed, return default
    logger.error("Failed to validate or extract valid JSON. Returning default.")
    return '{"decision": "allowed", "message": "", "chain_of_thought": "Failed to parse or extract JSON"}'