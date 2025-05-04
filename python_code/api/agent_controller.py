from agents import (GuardAgent,
                    ClassificationAgent,
                    DetailsAgent,
                    OrderTakingAgent,
                    RecommendationAgent,
                    AgentProtocol
                    )
import os
import pathlib # Import pathlib
from functools import lru_cache

# Get the directory where the current script is located
script_dir = pathlib.Path(__file__).parent.resolve()

# Construct paths relative to the script directory
rec_file1 = script_dir / 'recommendation_objects/apriori_recommendations.json'
rec_file2 = script_dir / 'recommendation_objects/popularity_recommendation.csv'

class AgentController():
    def __init__(self):
        # Initialize only necessary agents at startup
        self.guard_agent = GuardAgent()
        self.classification_agent = ClassificationAgent()
        
        # Store agent classes for lazy initialization
        self._recommendation_agent = None
        self._agent_instances = {}
        
        # Add a default agent to handle fallbacks
        self.default_agent = "details_agent"
    
    @property
    @lru_cache(maxsize=1)
    def recommendation_agent(self):
        # Lazy initialization of recommendation agent
        if self._recommendation_agent is None:
            self._recommendation_agent = RecommendationAgent(rec_file1, rec_file2)
        return self._recommendation_agent
    
    def _get_agent(self, agent_name):
        # Lazy initialization of agents
        if agent_name not in self._agent_instances:
            if agent_name == "details_agent":
                self._agent_instances[agent_name] = DetailsAgent()
            elif agent_name == "order_taking_agent":
                self._agent_instances[agent_name] = OrderTakingAgent(self.recommendation_agent)
            elif agent_name == "recommendation_agent":
                self._agent_instances[agent_name] = self.recommendation_agent
        return self._agent_instances.get(agent_name)
    
    def get_response(self, input):
        # Extract User Input
        job_input = input["input"]
        messages = job_input["messages"]

        # Get GuardAgent's response
        guard_agent_response = self.guard_agent.get_response(messages)
        if guard_agent_response["memory"]["guard_decision"] == "not allowed":
            return guard_agent_response
        
        # Get ClassificationAgent's response
        classification_agent_response = self.classification_agent.get_response(messages)
        chosen_agent = classification_agent_response["memory"].get("classification_decision", self.default_agent)

        # Validate that the chosen agent exists in our agent list
        if chosen_agent not in ["details_agent", "order_taking_agent", "recommendation_agent"]:
            chosen_agent = self.default_agent

        # Get the chosen agent's response
        agent = self._get_agent(chosen_agent)
        response = agent.get_response(messages)

        return response