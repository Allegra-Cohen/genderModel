from ogBargain_model import *
import matplotlib.pyplot as plt
import pandas

# agentPreferences: [{"name": roi}, alice, bob, ....]
# agentpmins: [alice, bob, alice, bob...]
# agentalphas: [alice, bob, alice, bob...]
# activityspecs: [{a:"name", "roi", "cost"}]
# portfoliospecs: [{"p", "activities": [name, name], "inputdict" {name: hours}}]

width = 4
height = 4
agentPreferences = [{"smoking": 0, "crops": 1}]*width*height*2
agentPmins = [0.6, 0.4]*8 + [0.4, 0.6]*8
agentAlphas = [0.2]*width*height*2
initialCoffers = [10]*width*height*2
activitySpecs = [{"name":"smoking", "roi":0, "cost":2}, {"name": "crops", "roi": 3, "cost": 1}]
portfolioSpecs = [{"p": 0.4, "activities": ["smoking", "crops"], "inputDict": {"smoking":0, "crops": 10}}, 
					{"p": 0.6, "activities": ["smoking", "crops"], "inputDict": {"smoking":2, "crops": 8}}]

insistence = 0 # 0.1

# One household/two agents per cell
model = Model(width, height, insistence, agentPreferences, agentPmins, agentAlphas, initialCoffers, activitySpecs, portfolioSpecs)
for i in range(30):
    model.step()

agent_db = model.datacollector.get_agent_vars_dataframe()
agent_db.to_csv('test_baseline', ',')

# print(agent_db)

# agent_db.loc[agent_db['tag']==1].pmin.plot()
# plt.show()