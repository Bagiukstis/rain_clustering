import pandas as pd
import seaborn as sb
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

df = pd.read_csv('../Data/weather-data.csv')
df = df.drop(columns=['name', 'precip', 'precipprob', 'preciptype', 'snow', 'snowdepth', 'sealevelpressure', 'solarradiation', 'solarenergy',
                      'uvindex', 'severerisk', 'icon', 'stations', 'windgust'])

df['conditions'].unique()
# Labeling good_w and bad_w hours
replacements = {'Partially cloudy': '0',
                'Overcast': '0',
                'Clear': '0',
                'Rain': '1',
                'Rain, Overcast': '1',
                'Rain, Partially cloudy': '1',
                'Snow, Rain, Overcast': '1',
                'Snow, Rain, Partially cloudy': '1',
                'Snow, Rain': '1',
                'Snow, Overcast': '1',
                'Snow, Partially cloudy': '1'}

df['conditions'] = df['conditions'].replace(replacements)
df['conditions'].value_counts()

# Converting to datetime format
df['datetime'] = pd.to_datetime(df['datetime'])

# Predicting 12 hours ahead:
df['future_weather_condition'] = df.conditions.shift(12, axis=0)

df = df.dropna()
df['conditions'] = df['conditions'].apply(np.int64)
df['future_weather_condition'] = df['future_weather_condition'].apply(np.int64)

# Correlation matrix
corr = df.corr(method='pearson')
sb.heatmap(corr, annot=True)
plt.show()

# Filtering columns which does not provide great value
df = df.drop(['feelslike', 'dew'], axis=1)

# Observing dependent value with other values and comparing the correlation
corr_t = df.corr(method='pearson')['future_weather_condition'].sort_values(ascending=True).drop(['future_weather_condition'])
corr_t.plot.bar()
plt.show()

# Timeseries temperature analysis
time = df['datetime']
temp = df['temp']
plt.plot(time, temp)
plt.show()
