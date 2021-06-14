import json
from flask import Flask,render_template,request
import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import os
import time
import requests

app = Flask(__name__)

def get_data():
    store_path = 'data.pkl'

    try:
        tm = os.path.getmtime(store_path) 
        if int(time.time())-int(tm) > 24 * 60 * 60:
            raise Exception("Cache expired")

        data = pd.read_pickle(store_path)
        return data
    except Exception as e:
        print (e)
        pass

    xl = requests.get('https://www.nrscotland.gov.uk/files//statistics/covid19/weekly-deaths-by-location-age-sex.xlsx')    
    with open('weekly-deaths-by-location-age-sex.xlsx','w') as f:
        f.write(xl.text)

    data_2021 = pd.read_excel ('weekly-deaths-by-location-age-sex.xlsx',
    sheet_name='Data',
            skiprows=4,
            skipfooter=2,
            usecols='A:F',
            header=None,
            names=['week','location','sex','age','cause','deaths']
            )

    data_2021['year'] = data_2021.week.str.slice(0,2).astype(int)
    data_2021['week'] = data_2021.week.str.slice(3,5).astype(int)

    xl = requests.get('https://www.nrscotland.gov.uk/files//statistics/covid19/weekly-deaths-by-location-age-group-sex-15-19.xlsx')    
    with open('weekly-deaths-by-location-age-group-sex-15-19.xlsx','w') as f:
        f.write(xl.text)

    data_1519 = pd.read_excel ('weekly-deaths-by-location-age-group-sex-15-19.xlsx',
            sheet_name='Data',
            skiprows=4,
            skipfooter=2,
            usecols='A:F',
            header=None,
            names=['year','week','location','sex','age','deaths'],
            #index_col=[1]
            )

    data_1519['cause'] = 'Non-COVID-19'

    data = data_1519.copy()
    data = data.append(data_2021)
    data.loc[data['age']==0,'age']='0'

    data.to_pickle(store_path)

    return data



def get_plot(pars=None):
    data = get_data()

    all_years = data['year'].unique()
    all_ages = data['age'].unique()
    all_sexes = data['sex'].unique()
    all_causes = data['cause'].unique()
    all_locations = data['location'].unique()

    years = list(map(int,pars[0].strip(',').split(','))) if pars else None
    ages = list(pars[1].strip(',').split(',')) if pars else None
    sexes = list(pars[2].strip(',').split(',')) if pars else None
    locations = list(pars[3].strip(',').split(',')) if pars else None
    causes = list(pars[4].strip(',').split(',')) if pars else None

    if years:
        data = data[data['year'].isin(years)]
    if ages:
        data = data[data['age'].isin(ages)]
    if sexes:
        data = data[data['sex'].isin(sexes)]
    if locations:
        data = data[data['location'].isin(locations)]
    if causes:
        data = data[data['cause'].isin(causes)]

    dt1 = data.groupby(['year','week']).agg({'deaths':np.sum})
    dt1.reset_index(inplace=True)

    fig = px.line(dt1,x='week', y='deaths',line_group='year',color='year')

    fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print (all_years,all_ages,all_sexes,all_causes,all_locations)
    return fig,all_years,all_ages,all_sexes,all_causes,all_locations

@app.route('/mycovidash')
def init():
    fig,all_years,all_ages,all_sexes,all_causes,all_locations = get_plot()
    return render_template('mycovidash.html',fig=fig,all_years=all_years,all_ages=all_ages,all_sexes=all_sexes,all_causes=all_causes,all_locations=all_locations)

@app.route('/mycovidash/update')
def update():
    fig,all_years,all_ages,all_sexes,all_causes,all_locations = get_plot([request.args.get('years',''),
                        request.args.get('ages',''),
                        request.args.get('sexes',''),
                        request.args.get('locations',''),
                        request.args.get('causes',''),
                        ])
    return fig