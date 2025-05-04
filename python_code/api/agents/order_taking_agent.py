import os
import json
import logging
from .utils import get_chatbot_response, double_check_json_output
from openai import OpenAI
import re
from copy import deepcopy
# from functools import lru_cache # Removed unused import
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO) # Keep INFO level for now, can be changed via env var
logger = logging.getLogger("order_taking_agent")

class OrderTakingAgent():
    def __init__(self, recommendation_agent):
        self.client = OpenAI(
            api_key=os.getenv("RUNPOD_TOKEN"),
            base_url=os.getenv("RUNPOD_CHATBOT_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME")

        self.recommendation_agent = recommendation_agent
        
        # Valid menu items (lowercase key -> canonical name)
        self.menu_items = {
            "cappuccino": "Cappuccino",
            "jumbo savory scone": "Jumbo Savory Scone",
            "latte": "Latte",
            "chocolate chip biscotti": "Chocolate Chip Biscotti",
            "espresso shot": "Espresso shot",
            "hazelnut biscotti": "Hazelnut Biscotti",
            "chocolate croissant": "Chocolate Croissant",
            "dark chocolate": "Dark chocolate",
            "cranberry scone": "Cranberry Scone",
            "croissant": "Croissant",
            "almond croissant": "Almond Croissant",
            "ginger biscotti": "Ginger Biscotti",
            "oatmeal scone": "Oatmeal Scone",
            "ginger scone": "Ginger Scone",
            "chocolate syrup": "Chocolate syrup",
            "hazelnut syrup": "Hazelnut syrup",
            "carmel syrup": "Carmel syrup",
            "sugar free vanilla syrup": "Sugar Free Vanilla syrup",
            "roti":"ROTI",
        }
        
        # Price lookup (canonical name -> price)
        self.price_lookup = {
            "Cappuccino": 14.50,
            "Jumbo Savory Scone": 13.25,
            "Latte": 14.75,
            "Chocolate Chip Biscotti": 12.50,
            "Espresso shot": 12.00,
            "Hazelnut Biscotti": 12.75,
            "Chocolate Croissant": 13.75,
            "Dark chocolate": 15.00,
            "Cranberry Scone": 13.50,
            "Croissant": 13.25,
            "Almond Croissant": 14.00,
            "Ginger Biscotti": 12.50,
            "Oatmeal Scone": 13.25,
            "Ginger Scone": 13.50,
            "Chocolate syrup": 11.50,
            "Hazelnut syrup": 11.50,
            "Carmel syrup": 11.50,
            "Sugar Free Vanilla syrup": 11.50,
            "ROTI": 5.50
        }
        
        self._quantity_pattern_cache = {} # Cache for compiled regex
        
        # Pre-processed menu keys sorted by length (desc) for matching
        self._all_matches = {**self.menu_items}
        self._sorted_matches = sorted(self._all_matches.keys(), key=len, reverse=True)
        
        self._system_prompt = None # Cache for system prompt

    # Method removed as it's no longer used after extract_potential_items refactor
    # def _get_quantity_pattern(self, item_key):
    #     if item_key not in self._quantity_pattern_cache:
    #         self._quantity_pattern_cache[item_key] = re.compile(r'(\d+)\s+(?:' + re.escape(item_key) + ')')
    #     return self._quantity_pattern_cache[item_key]

    # Method removed as it's no longer used after extract_potential_items refactor
    # def _extract_quantity(self, text, item_key):
    #     # Use cached compiled regex pattern
    #     pattern = self._get_quantity_pattern(item_key)
    #     match = pattern.search(text)
    #     return int(match.group(1)) if match else 1

    def extract_potential_items(self, message_text):
        """Extracts potential menu items and quantities from user message using a more robust method."""
        message_text_lower = message_text.lower()
        matched_items = {}
        processed_indices = set()
        word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10} # Add more if needed

        # Iterate through menu keys, longest first to prioritize specific matches
        for key in self._sorted_matches:
            # Pattern to find the item key, possibly pluralized, bounded by spaces or start/end of string.
            key_pattern = re.compile(r'(?:^|\s|\W)' + re.escape(key) + r'(?:s)?(?:$|\s|\W)', re.IGNORECASE) # Use \W for non-word boundaries

            for match in key_pattern.finditer(message_text_lower):
                # Adjust start/end to exclude the boundary characters matched by (^|\s|\W) and ($|\s|\W)
                match_start, match_end = match.span()
                item_start = match_start + (1 if match.group(0)[0].isspace() or not match.group(0)[0].isalnum() else 0)
                item_end = match_end - (1 if match.group(0)[-1].isspace() or not match.group(0)[-1].isalnum() else 0)

                # Check if this span overlaps with an already processed span
                if any(i in processed_indices for i in range(item_start, item_end)):
                    logger.debug(f"Skipping overlapping match for '{key}' at span ({item_start}, {item_end})")
                    continue # Skip overlapping matches

                item_name = self._all_matches[key] # Get canonical name

                # Look backwards from the item start for a quantity
                search_window_start = max(0, item_start - 20) # Look back up to 20 chars
                preceding_text = message_text_lower[search_window_start:item_start].strip()
                logger.debug(f"Item: '{key}', Preceding text: '{preceding_text}'")

                quantity = 1 # Default quantity
                # Try to find a number (digits) at the end of the preceding text
                qty_match_digits = re.search(r'(\d+)$', preceding_text)
                # Try to find number words at the end
                qty_match_words = re.search(r'(one|two|three|four|five|six|seven|eight|nine|ten)$', preceding_text, re.IGNORECASE)
                # Try to find 'a' or 'an' at the end
                qty_match_article = re.search(r'(?:a|an)$', preceding_text, re.IGNORECASE)

                if qty_match_digits:
                    quantity = int(qty_match_digits.group(1))
                    logger.debug(f"Found quantity (digits): {quantity} for '{key}'")
                elif qty_match_words:
                    quantity = word_to_num.get(qty_match_words.group(1).lower(), 1)
                    logger.debug(f"Found quantity (word): {quantity} for '{key}'")
                elif qty_match_article:
                    quantity = 1
                    logger.debug(f"Found quantity (article): {quantity} for '{key}'")
                else:
                     logger.debug(f"No specific quantity found for '{key}', defaulting to 1.")


                # Add or update quantity in matched_items
                matched_items[item_name] = matched_items.get(item_name, 0) + quantity
                logger.debug(f"Updated matched_items: {matched_items}")

                # Mark item span as processed
                processed_indices.update(range(item_start, item_end))
                logger.debug(f"Processed indices updated: {processed_indices}")

        # Create the final items list
        potential_items = []
        for item_name, quantity in matched_items.items():
            price_per_unit = self.price_lookup.get(item_name, 10.00) # Use default price if lookup fails
            price = price_per_unit * quantity
            potential_items.append({
                "item": item_name,
                "quantity": quantity,
                "price": f"RM{price:.2f}"
            })

        if potential_items:
             logger.debug(f"Extracted: {json.dumps(potential_items)}")

        return potential_items

    # _extract_quantity method removed as it's unused

    def update_order(self, current_order, new_items):
        """Update the order with new items, merging similar items and avoiding duplicates"""
        if not current_order:
            current_order = []
            
        # Process new items, merging with existing ones
        for new_item in new_items:
            # Basic validation: ensure new_item is a dict with 'item' key
            if not isinstance(new_item, dict) or "item" not in new_item:
                logger.warning(f"Skipping invalid new_item structure: {new_item}")
                continue

            # Normalize item name for comparison
            normalized_name = new_item["item"].lower()
            
            # Check if item already exists in order
            found = False
            for existing in current_order:
                # Compare using the canonical item name directly
                if existing.get("item") == new_item.get("item"):
                    # Update quantity
                    existing["quantity"] = existing.get("quantity", 1) + new_item.get("quantity", 1)
                    # Update price based on new quantity
                    price_per_unit = self.price_lookup.get(existing["item"], 10.00)
                    existing["price"] = price_per_unit * existing["quantity"]
                    found = True
                    break
            
            # If item not found, add it to the order
            if not found:
                current_order.append(new_item)
        
        # logger.debug(f"Updated order: {current_order}")
        return current_order

    @property
    def system_prompt(self):
        if self._system_prompt is None:
            self._system_prompt = """
            You are a customer support Bot for "Old Kasturi" coffee shop.

            Key Instructions:
            - DO NOT ask about payment methods (cash/card) or tell the user to go to the counter/pickup location.
            - Maintain the complete order history. Update quantities for existing items, don't duplicate. Add new items. Never delete unless asked.
            - Handle typos/misspellings (e.g., "scavy scone" -> "savory scone").
            - Use the "order" and "step number" from the memory section in the user message to track progress.

            Task Flow:
            1. Take the order, validate items against the menu (use internal price list).
            2. If invalid items, inform user and repeat valid order.
            3. Ask if anything else is needed. If yes, repeat from step 1.
            4. If no, finalize: list items/prices, calculate total, thank user, and end conversation.

            Output Format (Strict JSON):
            {
            "chain of thought": "Your reasoning: current step, user input analysis, response plan considering restrictions.",
            "step number": "Current task step number (string).",
            "order": "[{\"item\": \"item_name\", \"quantity\": quantity_num, \"price\": \"RMXX.XX\"}] (list of item dicts).",
            "response": "Your response to the user (string)."
            }

            IMPORTANT: You MUST return ONLY the JSON structure above. Do NOT include any introductory text, explanations, apologies, or any other text outside of the JSON object itself. Your entire response must be the valid JSON object.
        """
        return self._system_prompt

    def get_response(self, messages):
        messages = deepcopy(messages)
        logger.debug("Processing request with %d messages", len(messages))

        logger.info(f"Raw user message content: {messages[-1]['content']}") # <-- ADDED FOR DEBUGGING
        step_number = "1"
        asked_recommendation_before = False
        current_order = []

        # Look back through recent messages for last order state
        max_message_history = 10
        for message_index in range(len(messages) - 1, max(0, len(messages) - max_message_history - 1), -1):
            message = messages[message_index]
            if message["role"] == "assistant" and message.get("memory", {}).get("agent") == "order_taking_agent":
                step_number = message["memory"].get("step number", "1")
                order = message["memory"].get("order", [])
                asked_recommendation_before = message["memory"].get("asked_recommendation_before", False)
                if order:
                    current_order = order
                    logger.debug(f"Found prior order state: {json.dumps(current_order)}")
                    break

        # --- Get Previous State (Keep this part) ---
        # (Code from lines 240-252 finds previous order state)
        logger.debug(f"Previous order state found: {json.dumps(current_order)}")

        # --- DO NOT Update Order Before LLM Call ---
        # REMOVED: Item extraction and pre-emptive order update
        # user_message = messages[-1]['content'].lower()
        # try:
        #     potential_items = self.extract_potential_items(user_message)
        #     if potential_items:
        #         current_order = self.update_order(current_order, potential_items)
        #         logger.debug(f"Order after extraction/update: {json.dumps(current_order)}")
        # except Exception as e:
        #     logger.error(f"Error extracting items: {str(e)}")

        # --- Prepare Input for LLM ---
        # Send the PREVIOUS order state to the LLM
        last_order_taking_status = f"""
        PREVIOUS step number: {step_number}
        PREVIOUS order: {json.dumps(current_order)}
        """
        # Combine previous state with the LATEST user message
        enriched_message = last_order_taking_status + " \n User message: " + messages[-1]['content']
        # Replace last message content with enriched version for LLM context
        messages[-1]['content'] = enriched_message
        logger.info(f"Enriched message for LLM: {enriched_message}") # <-- Changed to INFO

        # Limit message history sent to LLM (Keep this part)
        input_messages = [{"role": "system", "content": self.system_prompt}] + messages[-min(max_message_history, len(messages)):]

        logger.debug(f"Sending messages to LLM: {json.dumps(input_messages)}")
        chatbot_output = get_chatbot_response(self.client, self.model_name, input_messages, temperature=0.1)
        logger.info(f"RAW LLM output received: {chatbot_output}") # <-- Log raw output

        # REMOVED call to double_check_json_output
        # logger.debug(f"Output after JSON check: {chatbot_output}") # REMOVED

        # Pass raw output directly to postprocess
        return self.postprocess(chatbot_output, messages, asked_recommendation_before, current_order)

    def postprocess(self, output_str, messages, asked_recommendation_before, current_order=[]):
        """Processes the LLM output, validates order, and formats the final response."""
        logger.info(f"Postprocessing raw LLM output: {output_str}") # <-- Changed to INFO

        # Attempt to extract JSON object if LLM included extra text
        json_match = re.search(r'({[\s\S]*})', output_str)
        if json_match:
            output_str = json_match.group(0)
            logger.debug(f"Extracted JSON part: {output_str}")
        else:
            logger.warning("Could not find JSON object in LLM output.")
            # Proceed with original string, likely causing JSONDecodeError below

        output = {}
        try:
            # REMOVED: Attempt to fix common JSON syntax errors

            # Attempt to parse the (potentially extracted) JSON string
            logger.info(f"Attempting to parse JSON string: {output_str}") # <-- ADDED FOR DEBUGGING
            output = json.loads(output_str)
            logger.info(f"Successfully parsed JSON. Parsed data type: {type(output)}") # <-- ADDED FOR DEBUGGING
            # Basic validation for essential keys from LLM
            if not all(k in output for k in ["step number", "order", "response"]):
                 logger.warning(f"Parsed JSON missing essential keys: {output_str}")
                 # Let it fall through to the exception handler to use fallback
                 raise json.JSONDecodeError("Parsed JSON missing essential keys", output_str, 0)
            logger.info("JSON parsing and key validation successful.") # <-- ADDED FOR DEBUGGING

        except json.JSONDecodeError as e:
            logger.warning(f"JSONDecodeError in postprocess: {e}. Using fallback.")
            # Simplified fallback
            return {
                "role": "assistant",
                "memory": { # Preserve memory as much as possible on error
                    "agent": "order_taking_agent",
                    "step number": "1",
                    "order": current_order,
                    "asked_recommendation_before": asked_recommendation_before
                },
                "response": "I'm sorry, I had trouble processing that. Could you please repeat your request?"
            }

        # --- Price/Quantity Validation ---
        # Start validation using the order list provided BY THE LLM in its output,
        # but apply OUR internal price/quantity checks to prevent hallucination.
        llm_order = output.get("order", []) # Get order from parsed LLM output
        temp_validated_order = []

        # --- START: Handle if LLM returns order as a string ---
        if isinstance(llm_order, str):
            logger.debug("LLM order field is a string. Attempting to parse.")
            try:
                llm_order = json.loads(llm_order) # Try parsing the string
                logger.debug(f"Successfully parsed string into list: {llm_order}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM order string: {e}. Resetting order.")
                llm_order = [] # Reset if parsing fails
        # --- END: Handle if LLM returns order as a string ---
        logger.info(f"LLM proposed order (before validation): {json.dumps(llm_order)}") # <-- ADDED FOR DEBUGGING

        if isinstance(llm_order, list):
            for item in llm_order: # Iterate through the LLM's proposed order (now guaranteed to be a list or reset to [])
                if isinstance(item, dict) and "item" in item:
                    item_name_from_llm = item.get("item")
                    canonical_name = None # Variable to store the correct key from price_lookup

                    # Case-insensitive check against price_lookup keys
                    if item_name_from_llm: # Ensure we have a name
                        item_name_lower = item_name_from_llm.lower()
                        logger.debug(f"Validating LLM item: '{item_name_from_llm}' (lowercase: '{item_name_lower}')") # DEBUG ADDED
                        for lookup_key in self.price_lookup:
                            logger.debug(f"  Comparing with price_lookup key: '{lookup_key}' (lowercase: '{lookup_key.lower()}')") # DEBUG ADDED
                            if lookup_key.lower() == item_name_lower:
                                canonical_name = lookup_key # Found match, store the canonical key
                                logger.debug(f"  Found match! Canonical name: '{canonical_name}'") # DEBUG ADDED
                                break
                        # DEBUG ADDED - Log if no match found after loop
                        if not canonical_name:
                            logger.debug(f"  No match found for '{item_name_from_llm}' in price_lookup keys.")

                    if canonical_name: # If a match was found (case-insensitive)
                        try:
                            quantity = int(item.get("quantity", 1))
                        except (ValueError, TypeError):
                            quantity = 1
                        price_per_unit = self.price_lookup[canonical_name] # Use canonical name for lookup
                        # Create validated item structure with canonical name and recalculated price
                        validated_item = {
                            "item": canonical_name, # Use the canonical name in the final order
                            "quantity": quantity,
                            "price": f"RM{price_per_unit * quantity:.2f}" # Calculate price based on validated quantity
                        }
                        temp_validated_order.append(validated_item)
                    else:
                        # Log if item not found even with case-insensitive check
                        logger.warning(f"Item '{item_name_from_llm}' not found in price_lookup (case-insensitive). Removing.")
                else:
                    # Log if item structure from LLM is invalid
                    logger.warning(f"Invalid item structure in LLM order: {item}. Skipping.")
        else:
             # Log if the order structure from LLM is not a list
             logger.warning(f"LLM order is not a list: {llm_order}. Resetting.")
             temp_validated_order = [] # Indented under else
        validated_order = temp_validated_order # This now holds the LLM's order after our validation - Outside else
        logger.info(f"Validated order (after internal checks): {json.dumps(validated_order)}") # <-- ADDED FOR DEBUGGING - Outside else


        # --- Final Output Assembly ---
        # Use the validated order derived from the LLM's output + our checks
        output["order"] = validated_order

        # Ensure memory contains the correct, validated information
        output["memory"] = {
            "agent": "order_taking_agent",
            "step number": str(output.get("step number", "1")), # Use LLM step number if valid, else default
            "order": validated_order,
            "asked_recommendation_before": asked_recommendation_before
        }
        output["role"] = "assistant"

        # Filter output to allowed keys, ensuring consistency
        allowed_keys = {"chain of thought", "step number", "order", "response", "memory", "role"}
        final_output = {k: v for k, v in output.items() if k in allowed_keys}

        logger.info(f"Final output: {json.dumps(final_output)}") # <-- Changed to INFO
        return final_output
