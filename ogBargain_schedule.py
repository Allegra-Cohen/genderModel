from collections import defaultdict
from mesa.time import RandomActivation
import numpy as np


class RandomActivationByHousehold(RandomActivation):

    def __init__(self, model):
        super().__init__(model)
        self.agents_by_type = defaultdict(dict)

    def add(self, agent):

        self._agents[agent.unique_id] = agent
        agent_class = agent.type #type(agent)
        self.agents_by_type[agent_class][agent.unique_id] = agent

    def remove(self, agent):

        del self._agents[agent.unique_id]

        agent_class = type(agent)
        del self.agents_by_type[agent_class][agent.unique_id]

    def step(self, byHousehold=True):
        if byHousehold:
            # shuffle the households
            household_keys = list(self.agents_by_type["household"].keys())
            np.random.shuffle(household_keys)
            for householdAgentKey in household_keys:
                householdAgent = self.agents_by_type["household"][householdAgentKey]
                householdAgent.step()
                householdAgent.alice.step()
                householdAgent.bob.step()
            self.steps += 1
            self.time += 1
        else:
            super().step()