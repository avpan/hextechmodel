import numpy as np
import os.path
from datetime import date, timedelta
import json
import pandas as pd
import time

#checks for whether or not the game is a good match to analyze
#it checks to see if the game has 10 players (no afks)
#it checks if the game is a rank game
def checkGame(matchNum):
    
    teamRed, teamBlue = False,False #blue = teamid 100 and red is 200
    #open match json file
    f = open("./data/real_data/match_%d.json"%matchNum,"r")
    data = json.load(f)
    
    if data['queueType'] != 'TEAM_BUILDER_DRAFT_RANKED_5x5':
        game = False
    else:
        partic_df = pd.DataFrame(data['participants'])
        
        #check if game has 10 players
        if partic_df['participantId'].count() == 10:
            game = True
        else:
            game = False

        for item in data:
            if item == 'timeline':
                game = True
                break
            else:
                game = False
                
        #due to new remake policy games that end before 5min are due to this
        game_length = data['matchDuration']/60.0 
        if game_length > 5.0:
            game = True
        else:
            game = False
    return game

def findDiffNumeric(metric, blue, red):
    total_metric_blue = sum([item[metric] for item in blue])
    total_metric_red = sum([item[metric] for item in red])
    metric_diff = total_metric_blue - total_metric_red
    return metric_diff

def getTotal(metric, data):
    total_metric = sum([item[metric] for item in data])    
    return total_metric

def findDiffBool(metric, team):
    metric_list = [item[metric] for item in team]
    metricTrueFalse = any(metric_list)
    return metricTrueFalse

def main(matchNum):
    f = open("./data/real_data/match_%d.json"%matchNum,"r")
    data = json.load(f)

    player_info = []
    for item in data['participantIdentities']:
        playerid = int(item['participantId'])
        name = item['player']['summonerName']
        player_info.append((id,name))

    df1 = pd.DataFrame(data['participants'])
    df2 = pd.DataFrame(data['teams'])
    
    #determine basic stats of winning team
    victory_team = None
    defeat_team = None
    for i in range(2):
        df = df2.iloc[i]
        if df['winner']:
            victory_team = df2.iloc[[i]]
        else:
            defeat_team = df2.iloc[[i]]
            
    #separate winners and losers
    winners, losers = [],[]
    for i in range(10):
        df = df1.iloc[i]
        playerId = df['participantId']
        item = df['stats']
        rank = df['highestAchievedSeasonTier']    
        kills = item['kills']
        deaths = item['deaths']
        assists = item['assists']
        gold = item['goldEarned']
        cs = item['minionsKilled'] + item['neutralMinionsKilledTeamJungle'] + item['neutralMinionsKilledEnemyJungle'] + item['neutralMinionsKilled']
        if item['winner']:
            item['ID'] = playerId
            item['rank'] = rank
            winners.append(item)
            #winners.append({'ID': playerId, 'rank': rank, 'kills': kills, 'deaths': deaths, 'assists': assists, 'gold':gold, 'creep_score':cs})
        else:
            item['ID'] = playerId
            item['rank'] = rank
            losers.append(item)
            #losers.append({'ID': playerId, 'rank': rank, 'kills': kills, 'deaths': deaths, 'assists': assists, 'gold':gold, 'creep_score':cs})
            
    game_length = data['matchDuration']/60.0 
    victory_team.reset_index(inplace=True,drop=True)
    defeat_team.reset_index(inplace=True,drop=True)

    if 'bans' in victory_team.columns:
        victory_team = victory_team.drop('bans',axis=1)
    if 'bans' in defeat_team.columns:
        defeat_team = defeat_team.drop('bans',axis=1)
    
    goldDiff = findDiffNumeric('goldEarned',winners,losers)
    goldTotal = getTotal('goldEarned',winners)
    killTotal = getTotal('kills',winners)    
    killDiff = findDiffNumeric('kills',winners,losers)
    towerDiff = victory_team.loc[0,'towerKills'] - defeat_team.loc[0,'towerKills']
    baronDiff = victory_team.loc[0,'baronKills'] - defeat_team.loc[0,'baronKills']
    dragonDiff = victory_team.loc[0,'dragonKills'] - defeat_team.loc[0,'dragonKills']
    inhibitorDiff = victory_team.loc[0,'inhibitorKills'] - defeat_team.loc[0,'inhibitorKills']
    
    victory_team.insert(victory_team.shape[1],'gameLength',game_length)
    victory_team.insert(victory_team.shape[1],'goldTotal',goldTotal)
    victory_team.insert(victory_team.shape[1],'goldDiff',goldDiff)
    victory_team.insert(victory_team.shape[1],'killTotal',killTotal)
    victory_team.insert(victory_team.shape[1],'killDiff',killDiff)
    victory_team.insert(victory_team.shape[1],'towerDiff',towerDiff)
    victory_team.insert(victory_team.shape[1],'inhibitorDiff',inhibitorDiff)
    victory_team.insert(victory_team.shape[1],'baronDiff',baronDiff)
    victory_team.insert(victory_team.shape[1],'dragonDiff',dragonDiff)
    
    goldTotal = getTotal('goldEarned',losers)
    killTotal = getTotal('kills',losers)
    killDiff = findDiffNumeric('kills', losers, winners)
    goldDiff = findDiffNumeric('goldEarned',losers,winners)    
    towerDiff = defeat_team.loc[0,'towerKills'] - victory_team.loc[0,'towerKills']
    baronDiff = defeat_team.loc[0,'baronKills'] - victory_team.loc[0,'baronKills']
    dragonDiff = defeat_team.loc[0,'dragonKills'] - victory_team.loc[0,'dragonKills']
    inhibitorDiff = defeat_team.loc[0,'inhibitorKills'] - victory_team.loc[0,'inhibitorKills']
    
    defeat_team.insert(defeat_team.shape[1],'gameLength',game_length)
    defeat_team.insert(defeat_team.shape[1],'goldTotal',goldTotal)
    defeat_team.insert(defeat_team.shape[1],'goldDiff',goldDiff)
    defeat_team.insert(defeat_team.shape[1],'killTotal',killTotal)
    defeat_team.insert(defeat_team.shape[1],'killDiff',killDiff)
    defeat_team.insert(defeat_team.shape[1],'towerDiff',towerDiff)
    defeat_team.insert(defeat_team.shape[1],'inhibitorDiff',inhibitorDiff)
    defeat_team.insert(defeat_team.shape[1],'baronDiff',baronDiff)
    defeat_team.insert(defeat_team.shape[1],'dragonDiff',dragonDiff)    
    
    #combine the victory and losing teams
    match_df = victory_team.append(defeat_team)
    #write to file
    if matchNum == 1:
        with open("./data/test_data/prelim_data.csv",'wb') as f:
            match_df.to_csv(f,header=True)
    else:
        with open("./data/test_data/prelim_data.csv",'a') as f:
            match_df.to_csv(f,header=False)
        
        
if __name__ == "__main__":
    N_matches = int(raw_input("How many matches to convert?"))
    for n in range(N_matches+1):
        filepath = "./data/real_data/match_%d.json" % n
        if os.path.isfile(filepath):
            #print n
            if checkGame(n):
                main(n)
            else:
                continue
            