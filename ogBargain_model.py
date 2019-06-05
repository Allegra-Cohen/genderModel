# model.py
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.time import StagedActivation
import numpy as np
import random
import operator
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from ogBargain_schedule import *


class Model(Model):
	def __init__(self, width, height, insistence, agentPreferences, agentPmins, agentAlphas, initialCoffers, activitySpecs, portfolioSpecs):

		self.insistence = insistence
		activityDict = {}
		portfolios = []
		for a in activitySpecs: # [{a},{a}]
			activityDict[a["name"]] = (Activity("a_" + str(a["name"]), a["roi"], a["cost"], self)) # Turn specs into Activity objects
		for i in range(len(portfolioSpecs)): # {p: p, "activities": nameList ["smoking", "crops"], inputDict {"aName": hours}}
			portfolios.append(Portfolio("p_" + str(i), portfolioSpecs[i]["p"], [activityDict[aName] for aName in portfolioSpecs[i]["activities"]], portfolioSpecs[i]["inputDict"], self)) # Turn portfolio specs into Portfolio objects with Activity objects

		# self.running = True
		self.grid = MultiGrid(width, height, True) # bool = toroidal
		self.schedule = RandomActivationByHousehold(self)

		houseCount, agentCount = 0, 0
		for i in range(width):
			for j in range(height):
				alice = Member("m_" + str(agentCount), 0, houseCount, agentPreferences[agentCount], agentPmins[agentCount], agentAlphas[agentCount], self) # ID, tag, household, preferences, pmin, model
				bob = Member("m_" + str(agentCount + 1), 1, houseCount, agentPreferences[agentCount+1], agentPmins[agentCount+1], agentAlphas[agentCount+1], self) 
				h = Household("h_" + str(houseCount), alice, bob, initialCoffers[houseCount], portfolios, self) 
				alice.household = h
				bob.household = h
				self.schedule.add(h)
				self.schedule.add(alice)
				self.schedule.add(bob)
				self.grid.place_agent(h, (i, j))
				self.grid.place_agent(alice, (i, j))
				self.grid.place_agent(bob, (i, j))
				houseCount += 1
				agentCount += 2

				# print(h.unique_id, h.alice.unique_id, h.bob.unique_id, alice.household.unique_id, bob.household.unique_id)

		# print(self.schedule.agents)

		self.datacollector = DataCollector(
			# model_reporters={"Gini": compute_gini},  # A function to call
			agent_reporters={"pmin": lambda x: x.pmin if x.type == "member" else None,
			 "tag": lambda x: x.tag if x.type == "member" else None,
			 "insistent": lambda x: x.insistent[len(x.insistent)-1] if x.type == "member" else None,
			 "householdID": lambda x: x.household.unique_id if x.type == "member" else x.unique_id,
			 "coffer": lambda x: x.coffer if x.type == "household" else None,
			 "penaltyProp": lambda x: x.penalty if x.type == "household" else None,
			 "portChosen": lambda x: x.choice if x.type == "household" else None})  # An agent attribute

	def step(self):
		self.datacollector.collect(self)
		self.schedule.step()


class Activity(Agent):
	def __init__(self, unique_id, roi, cost, model):
		super().__init__(unique_id, model)
		self.cost = cost
		self.roi = roi # $ per (capital * labor)


class Portfolio(Agent):
	def __init__(self, unique_id, p, activities, inputDict, model):
		super().__init__(unique_id, model)
		self.activities = activities # Activity.cost, Activity.roi
		self.p = [1-p, p]
		self.inputDict = inputDict

	# OtherV, otherP are the expected value and portion for the agent, myV is the current portfolio's expected value for that agent.
	# V's are different depending on if you are Alice or Bob.
	def calculateEquivalentP(self, otherV, otherP, myV):
		delta = min(otherV, myV)/float(max(otherV, myV)) # See how much bigger one is than the other
		return(delta*otherP) # This is the portion that Bob gets if they go with this portfolio.


	def payoff(self):
		payoff = 0
		for a in self.activities:
			payoff += a.roi*(self.inputDict[a.unique_id[2:]]) - a.cost # COMMUNAL VERSION
		return payoff


# Primary unit. Agents can update their own inputs from here but bargains and neighborhoods are
# handled in the household.
class Household(Agent):
	def __init__(self, unique_id, a1, a2, coffer, portfolios, model):
		super().__init__(unique_id, model)
		self.type = "household"
		self.alice = a1
		self.bob = a2
		self.coffer = coffer
		self.portfolios = portfolios
		self.choice = 0
		# self.choices = [""]
		self.penalty = 0
		# self.penalties = [""]

	def step(self):
		# print("HOUSEHOLD ", self.unique_id)
		portfolio = self.spousalBargain(self.portfolios, False)
		# self.alice.step()
		# self.bob.step()
		self.getPayoff(portfolio)


	def sweeten(self, bribeRange, payoffsB, prefA, penalty, verbal):
		needed = self.bob.pmin*payoffsB[prefA]
		if needed <= max(bribeRange):
			if verbal: print("Alice offers: ", needed, " which is an increase of ", needed - penalty*payoffsB[prefA])
			return self.bob.pmin
		else:
			if verbal: print("Alice needed",needed, " which is an increase of ", needed - penalty*payoffsB[prefA], ", can't sweeten.")
			return None 


	def spousalBargain(self, portfolios, verbal):
		payoffsA = self.alice.expectedPayoff(portfolios) # What Alice and Bob think the total payoff of each portfolio will be.
		payoffsB = self.bob.expectedPayoff(portfolios)
		prefA, allotmentA = max(enumerate([pay*port.p[self.alice.tag] for pay, port in zip(payoffsA,portfolios)]), key=operator.itemgetter(1)) # Alice's preference and expected payoff.
		prefB, allotmentB = max(enumerate([pay*port.p[self.bob.tag] for pay, port in zip(payoffsB, portfolios)]), key=operator.itemgetter(1))  # Bob's preference and expected payoff.

		if verbal:
			print("Alice's initial preference: Portfolio ", prefA + 1, " with expected payoff ", round(allotmentA,2))
			print("Bob's initial preference: Portfolio ", prefB + 1, " with expected payoff ", round(allotmentB,2))

		if prefA != prefB:
			penalty = portfolios[prefA].calculateEquivalentP(payoffsB[prefB], portfolios[prefB].p[self.bob.tag], payoffsB[prefA]) # The share Alice has to give Bob of her preferred portfolio to ensure she gets it.
			p1Alice = (payoffsA[prefA])*(1 - penalty) # Alice's payoff from prefA if she pays a penalty.
			p2Alice = payoffsA[prefB]*(portfolios[prefB].p[self.alice.tag]) # Alice's payoff from Bob's preferred portfolio.
			bribeRange = [p2Alice, p1Alice] # What Alice has to bribe Bob with if they go with her preferred portfolio.

			if verbal:
				print("Bob's pmin is ", self.bob.pmin)
				print("The original p1* is ", penalty)
				print("Bob figures he'll get ", round(penalty*(payoffsB[prefA]),2), "which should be the same as ", round(allotmentB,2))
				print("Alice expects ", round(p1Alice,2) ," and has between ", str(round(bribeRange[1],2)), " and ", str(round(bribeRange[0],2)), " to bribe Bob further to choose Portfolio ", prefA + 1)
	
			if self.bob.pmin > penalty:
				if verbal: print("Bob's pmin is too large to accept the original deal.")
				# NOTE ========== Here's where an "unhappiness index" would be updated/make-or-break a marriage, etc.
				penalty = self.sweeten(bribeRange, payoffsB, prefA, penalty, verbal) # It'll be None if Alice doesn't have any room to move.
				if penalty == None: # If Alice can't do any better than what she offers and Bob wants more
					if verbal: print("Alice has to select ", prefB + 1)
					self.choice = prefB
					# self.choices.append(prefB)
					self.penalty = None
					# self.penalties.append(None)
					return prefB
			self.choice = prefA
			# self.choices.append(prefA)
			self.penalty = penalty
			# self.penalties.append(penalty)
			return prefA

		else:
			if verbal:
				print("Bob's pmin is ", self.bob.pmin)
				print("Bob and Alice agree on Portfolio ", prefA + 1)
			self.choice = prefA
			# self.choices.append(prefA)
			self.penalty = penalty
			# self.penalties.append(None)
			return prefA

	def getPayoff(self, chosenPortfolio):
		payoff = self.portfolios[chosenPortfolio].payoff()
		self.coffer += payoff


class Member(Agent):
	def __init__(self, unique_id, tag, household, preferences, pmin, alpha, model):
		super().__init__(unique_id, model)
		self.type = "member"
		self.tag = tag # 0 = Alice, 1 = Bob
		self.household = household # This is the object
		self.preferences = preferences # {activityName: roi}
		self.pmin = pmin
		self.alpha = alpha
		self.divorced = False
		self.listenedTo = [""] # [Time[people]]

		self.insistent = [False]
		self.lastpmin = pmin

	def step(self):
		# print(self.unique_id, "AGENT")
		self.update()


	def expectedPayoff(self, portfolios):
		# This one assumes labor is communal:
		# inputDict["aName": hours] --> for aName in portfolio's input list, get expected payoff based on preference (aName:roi)*hours spent
		return [sum(self.preferences[activity]*x.inputDict[activity] for activity in x.inputDict.keys()) for x in portfolios]

	def update(self):
		agentList = []
		surroundingCells = self.model.grid.get_cell_list_contents(self.model.grid.get_neighborhood(self.pos, moore = True, include_center = False))
		for cell in surroundingCells:
			if cell.type == "member":
				if cell.tag == self.tag: # Only listen to your people:
					agentList.append(cell)

		sortedAgents = sorted(agentList, key=operator.attrgetter('household.coffer'))
		aboveAvg = np.mean([b.pmin for b in sortedAgents[int(len(sortedAgents)/2):len(sortedAgents)]])
		# self.pmin += self.alpha*(aboveAvg - self.pmin)
		# self.pmin = max(0, self.pmin)
		# self.pmin = min(1, self.pmin)
		# self.listenedTo.append([agent.unique_id for agent in sortedAgents[int(len(sortedAgents)/2):len(sortedAgents)]])

		if np.random.binomial(1, self.model.insistence):
			self.pmin = 1.0
			self.insistent.append(True)
		else:
			if self.insistent[self.model.schedule.time-1]:
				self.pmin = self.lastpmin
			self.pmin += self.alpha*(aboveAvg - self.pmin)
			self.pmin = max(0, self.pmin)
			self.pmin = min(1, self.pmin)
			self.insistent.append(False)
			self.lastpmin = self.pmin































