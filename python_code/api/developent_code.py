from agents import (GuardAgent,
                    ClassificationAgent,
                    DetailsAgent,
                    OrderTakingAgent,
                    RecommendationAgent,
                    AgentProtocol
                    )
import os
import pathlib # Import pathlib

# Get the directory where the current script is located
script_dir = pathlib.Path(__file__).parent.resolve()

# Construct paths relative to the script directory
rec_file1 = script_dir / 'recommendation_objects/apriori_recommendations.json'
rec_file2 = script_dir / 'recommendation_objects/popularity_recommendation.csv'

def main():
    guard_agent = GuardAgent()
    classification_agent = ClassificationAgent()
    recommendation_agent = RecommendationAgent(rec_file1, rec_file2)
    
    agent_dict: dict[str, AgentProtocol] = {
        "details_agent": DetailsAgent(),
        "order_taking_agent": OrderTakingAgent(recommendation_agent),
        "recommendation_agent": recommendation_agent
    }
    
    # Add a default agent to handle fallbacks
    default_agent = "details_agent"
    
    messages = []
    while True:
        # Display the chat history
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("\n\nPrint Messages ...............")
        for message in messages:
            print(f"{message['role'].capitalize()}: {message['content']}")

        # Get user input
        prompt = input("User: ")
        messages.append({"role": "user", "content": prompt})

        # Get GuardAgent's response
        guard_agent_response = guard_agent.get_response(messages)
        if guard_agent_response["memory"]["guard_decision"] == "not allowed":
            messages.append(guard_agent_response)
            continue
        
        # Get ClassificationAgent's response
        classification_agent_response = classification_agent.get_response(messages)
        chosen_agent = classification_agent_response["memory"].get("classification_decision", default_agent)
        
        # Validate that the chosen agent exists in our agent dictionary
        if chosen_agent not in agent_dict:
            print(f"Invalid agent selected: {chosen_agent}, using {default_agent} instead")
            chosen_agent = default_agent
        
        print("Chosen Agent: ", chosen_agent)

        # Get the chosen agent's response
        agent = agent_dict[chosen_agent]
        response = agent.get_response(messages)
        
        messages.append(response)


if __name__ == "__main__":
    main()