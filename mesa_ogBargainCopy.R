library('ggplot2')
library('sp')
library('data.table')

setwd("~/Documents/Allegra's Folders/School/thesis_thinking/dr_kiker/mesaCode/ogBargain/")

includingHouseholds <- data.frame(read.csv('test_baseline'))

justHouseholds <- includingHouseholds[grep('^h', includingHouseholds$AgentID),]
justMembers <- includingHouseholds[grep('^m', includingHouseholds$AgentID),]

bothAgents <- (merge(justHouseholds, justMembers, by = c("householdID", "Step")))
drops <- c("AgentID.x", "pmin.x", "tag.x", "insistent.x", "coffer.y", "penaltyProp.y", "portChosen.y")
bothAgents = bothAgents[ , !(names(bothAgents) %in% drops)]
names(bothAgents) = c("householdID", "Step", "coffer", "penaltyProp", "portChosen", "agentID", "pmin", "tag", "insistent")
data = bothAgents

data$portChosen[data$portChosen==0] = "Portfolio 1"
data$portChosen[data$portChosen==1] = "Portfolio 2"

mnpmin = round(mean(data$pmin[data$tag==1 & data$Step==max(data$Step) & data$pmin != 1.0]),2)
mnpmin

# Figure 1
graphMe = as.data.table(data)
graphMe[,("penaltyProp") := round(.SD,2), .SDcols="penaltyProp"]
graphMe$penaltyProp[is.na(graphMe$penaltyProp) & graphMe$Step > 0] = "No Deal"
graphMe$penaltyProp[graphMe$Step == 0] = "Initialization"
graphMe = as.data.frame(graphMe)
ggplot(graphMe[graphMe$tag ==1,], aes(x = Step, y = pmin, group = agentID, color = as.factor(penaltyProp))) +
  geom_line()+
  scale_colour_manual(values = bpy.colors(7))+#c( "forestgreen", "seagreen3", "rosybrown3", "orchid3", "orchid1", "grey40", "black")) +
  guides(color = guide_legend(title = "Proportion Offered\n by Female Agents"), lwd = guide_legend(override.aes = list(lwd=13))) +
  theme_bw() + theme(panel.border = element_blank(), panel.grid.major = element_blank(), panel.grid.minor = element_blank(), axis.line = element_line(colour = "black")) +
  theme(legend.position = c(0.9, 0.8), legend.text=element_text(size=12), legend.title=element_text(size=14))+
  xlab("Time") + ylab(expression("Male Agent P"["min"])) +
  annotate("text", label = mnpmin, x = 29.6, y = mnpmin + 0.003) 


# Figure 2
mnpmin = round(mean(data$pmin[data$tag==1 & data$time==max(data$Step) & data$pmin != 1.0]),2)
ggplot(data[data$tag==1,], aes(x = Step, y = pmin, group = agentID, color = as.factor(portChosen)))+
  #alpha = violent)) + 
  #geom_jitter(width = 0, height = 0.01) +
  geom_point()+
  scale_alpha_discrete(limits = c("True", "False")) +
  scale_colour_manual(values = bpy.colors(4)) + #c("grey40","orchid3", "forestgreen")) +
  theme_bw() + theme(panel.border = element_blank(), panel.grid.major = element_blank(), panel.grid.minor = element_blank(), axis.line = element_line(colour = "black")) +
  theme(legend.position = c(0.9, 0.82),legend.text=element_text(size=12), legend.title=element_text(size=14)) +
  xlab("Time") + ylab(expression("Male Agent P"["min"])) +
  scale_shape(guide = 'none') + guides(color=guide_legend(title="Portfolio Chosen"), alpha = 'none') +
  annotate("text", label = mnpmin, x = 29.6, y = mnpmin + 0.05) 