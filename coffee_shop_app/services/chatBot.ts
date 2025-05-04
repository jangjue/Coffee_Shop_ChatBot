import axios from 'axios';
import { MessageInterface } from '@/types/types';
import { API_KEY, API_URL } from '@/config/runpodConfigs';

async function callChatBotAPI(messages: MessageInterface[]): Promise<MessageInterface> {
    try {
        console.log("Sending messages to API:", JSON.stringify(messages, null, 2));
        const response = await axios.post(API_URL, {
            input: { messages }
        }, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`
            }
        });

        console.log("Raw API response:", JSON.stringify(response.data, null, 2));

        // Handle different response structures
        let outputMessage: MessageInterface;

        if (response.data && typeof response.data === 'object') {
            if (response.data.output) {
                // Standard structure: { output: { role, content, memory } }
                outputMessage = response.data.output;

                // If content is missing but response field exists, use response field
                if (response.data.output.response &&
                   (!response.data.output.content || response.data.output.content.trim() === '')) {
                    outputMessage.content = response.data.output.response;
                }
            } else if (response.data.role) {
                // Direct message structure: { role, content, memory }
                outputMessage = response.data;

                 // If content is missing but response field exists, use response field
                if (response.data.response &&
                   (!response.data.content || response.data.content.trim() === '')) {
                    outputMessage.content = response.data.response;
                }
            } else {
                // Unknown structure, create a fallback message
                outputMessage = {
                    role: 'assistant',
                    content: 'Sorry, I couldn\'t process your request properly.',
                    memory: {}
                };
            }
        } else {
            // Completely unexpected response
            outputMessage = {
                role: 'assistant',
                content: 'Sorry, I received an unexpected response format.',
                memory: {}
            };
        }

        // Ensure content is never empty
        if (!outputMessage.content || outputMessage.content.trim() === '') {
            // Try to use the 'response' field if available and content is empty
            // Removed check for outputMessage.response as it doesn't exist on MessageInterface
            // If content is empty, use the default fallback.
            if (false) { // Keep the else block structure, effectively always going to else
                 // This block is intentionally unreachable
            } else {
                 outputMessage.content = 'I apologize, but I don\'t have a specific response for that at the moment.';
            }
        }

        // Ensure memory exists
        if (!outputMessage.memory) {
            outputMessage.memory = {};
        }

        console.log("Processed output message:", outputMessage);
        return outputMessage;
    } catch (error: any) {
        console.error('Error calling the API:', error);

        // Return a friendly error message rather than throwing
        const errorMessage: MessageInterface = {
            role: 'assistant',
            content: `I'm sorry, there was an error processing your request: ${error.message || 'Unknown error'}`,
            memory: {}
        };

        return errorMessage;
    }
}

export { callChatBotAPI };