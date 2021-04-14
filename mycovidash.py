import json
from flask import Flask,render_template,request
import numpy as np
import pandas as pd
import plotly
import plotly.express as px

app = Flask(__name__)

def get_data():
    data_2021 = pd.read_excel ('https://www.nrscotland.gov.uk/files//statistics/covid19/weekly-deaths-by-location-age-sex.xlsx',
    sheet_name='Data',
            skiprows=4,
            skipfooter=2,
            usecols='A:F',
            header=None,
            names=['week','location','sex','age','cause','deaths']
            )

    data_2021['year'] = data_2021.week.str.slice(0,2).astype(int)
    data_2021['week'] = data_2021.week.str.slice(3,5).astype(int)

    data_1519 = pd.read_excel ('https://www.nrscotland.gov.uk/files//statistics/covid19/weekly-deaths-by-location-age-group-sex-15-19.xlsx',
            sheet_name='Data',
            skiprows=4,
            skipfooter=2,
            usecols='A:F',
            header=None,
            names=['year','week','location','sex','age','deaths'],
            )

    data_1519['cause'] = 'Non-COVID-19'

    data = data_1519.copy()
    data = data.append(data_2021)
    return data


def get_plot():
    data = get_data()

    dt1 = data.groupby(['year','week']).agg({'deaths':np.sum})
    dt1.reset_index(inplace=True)

    fig = px.line(dt1,x='week', y='deaths',line_group='year',color='year')

    fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return fig

@app.route('/')
def init():
    fig = get_plot()
    return render_template('mycovidash.html',fig=fig)

