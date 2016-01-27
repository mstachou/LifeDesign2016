# -*- coding: utf-8 -*-
"""
Created on Tue Jan  5 17:13:40 2016

@author: mstachou
"""
import sys
import os
import numpy as np
import pandas as pd

def read_json(file):
    with open(file, 'r') as f:
        dfj = pd.read_json(f)
   
    if dfj.empty: return
   
    dfj.index = pd.to_datetime(dfj.measured_at)
    dfj = dfj.tz_localize('GMT').tz_convert('Asia/Tokyo')
   
    dfj['value'] = dfj['value'].where( dfj['missing']==False, np.nan)
    dfj = dfj.interpolate(method='linear')
    dfj.insert(0, 'vdiff', dfj.value.diff())

    global last_value
    last_value = dfj.tail(1).ix[0,'value']
         
    del dfj['measured_at']    
    del dfj['value']

    return dfj.fillna(0.0)

def calc_diff(df):
    delta = 1    
    next = df.tail(48*delta).head(48)    
    next.index = next.index + pd.DateOffset(days=1)
    dayofweek = next.index[0].dayofweek
      
    mask1231 = df.index.dayofyear != pd.Timestamp('2015-12-31').dayofyear
    mask0101 = df.index.dayofyear != pd.Timestamp('2016-01-01').dayofyear
    mask = np.logical_and(mask1231, mask0101)
    
    #mask = df.index.dayofyear != next.index[0].dayofyear    
    dfc = df[mask]
    
    dfc = dfc.mask(dfc['missing']).dropna()
    dfg = dfc.groupby(dfc.index.dayofweek)
    dow = dfg.get_group(dayofweek)
    
    if dayofweek > 0 and dayofweek < 5:
        #dow = pd.concat([dow, df.tail(48*(delta+1)).head(48)], axis=0)    
        dow = pd.concat([dow, df.tail(48*delta).head(48)], axis=0)    
    
    dowg = dow.groupby([dow.index.hour, dow.index.minute]).mean()
    next.insert(0, 'new', dowg['vdiff'].tolist())
    next.insert(0, 'diff', (next['new'] - next['vdiff']).apply(np.square))
    del next['missing']
    return next

def out_json(df):
    df.insert(0, 'value', df['new'].cumsum().add(last_value))
    df.insert(0, 'missing', False)
    df.insert(0, 'measured_at', df.index.map(lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.000+09:00')))
    del df['vdiff']
    del df['diff']
    del df['new']
    return df.to_json(orient='records')
    
def main():

	argc = len(sys.argv)
	diffsum = 0

	if (argc == 2):
	    file = sys.argv[1]
	    df = read_json(file)
	    next = calc_diff(df)
	    print(out_json(next))
	    
	else:
	    os.chdir("C:\\Users\\mmachi\\Python\\lifeDesignOrg\\download\\")
	    house = [7,8,9,12,13,16,20,21,22,23,24,26,30,34,35]
	    #house = [7,8,9,12,13,16,20,21,22,23,24,30]
	    #house = [7,8,9,12,13,16]
	    #house = [26]
	    #month = [8,9,10,11]
	    month = [11]
	    for h in house:
	        for m in month:
	            file = '2015%02d_forward_integral_%d.json' % (m, h)
	            print(file)
	            df = read_json(file)
	            next = calc_diff(df)
	            print(next['diff'].sum())
	            
	            mask = df.index.dayofyear != next.index[0].dayofyear
	            dfm = df[mask]
	            dfm = dfm.groupby([dfm.index.hour, dfm.index.minute]).mean()
	            del dfm['missing']
	            next.insert(0, 'allmean', dfm['vdiff'].tolist())  
	            next.insert(0, 'alldiff', (next['allmean'] - next['vdiff']).apply(np.square))            
	            print(next['alldiff'].sum())
	            print(next['diff'].sum() - next['alldiff'].sum())
	            diffsum += next['diff'].sum() - next['alldiff'].sum()
	            
	    print(diffsum)

last_value = 0
if __name__ == '__main__':
    main()  
