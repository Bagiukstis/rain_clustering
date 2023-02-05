import os.path
import os
import json
import urllib.request
import urllib.error
import sys
import mlflow
import datetime
import pandas as pd
import numpy as np
import copy
# Comment when not running in a docker container
module_path = os.path.abspath('/k8s_rain_clustering/')
sys.path.insert(0, module_path)

from twilio.rest import Client
from config_db.connector import Connector
from sklearn.metrics import accuracy_score
import warnings
with warnings.catch_warnings():
    warnings.simplefilter(action='ignore', category=FutureWarning)

class Inference():
    def __init__(self):
        self.path = os.path.join(module_path, 'config_db/')
        #self.path = 'config_db/'
        self.connector = Connector(self.path + 'config_mysql.yaml', 'coat_project_local', 'alchemy')
        self.db = self.connector.connect()
        self._load_data()
        self.model = self._load_model()
        self.run()
        pass

    def _load_data(self):
        # If running locally

        #config_file = self.path + 'config.yaml'
        #config_file = os.environ['API_KEY']

        # with open(config_file, 'r') as yamlfile:
        #     data = yaml.load(yamlfile, Loader=yaml.FullLoader)

        # with kubernetes secrets
        api_key = os.environ['API_KEY']

        UnitGroup = 'metric'
        Location = 'Stuttgart'
        Include = "hours"
        ContentType = 'json'
        End_date = datetime.datetime.now()
        End_date = End_date.strftime('%Y-%m-%d')
        Start_date = datetime.datetime.now() - datetime.timedelta(days=1)
        Start_date = Start_date.strftime('%Y-%m-%d')

        base_url = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/'
        ApiQuery = base_url + Location

        if (len(Start_date)):
            ApiQuery += '/'+Start_date
            if (len(End_date)):
                ApiQuery += '/'+End_date

        ApiQuery += '?'

        if (len(UnitGroup)):
            ApiQuery += "&unitGroup=" + UnitGroup

        if (len(Include)):
            ApiQuery += "&include=" + Include

        # with default
        #ApiQuery += '&key=' + data['API_KEY']

        # with kubes
        ApiQuery += '&key=' + api_key

        if len(ContentType):
            ApiQuery += "&contentType" + ContentType

        try:
            data = urllib.request.urlopen(ApiQuery).read().decode('UTF-8')
        except urllib.error.HTTPError as e:
            ErrorInfo = e.read().decode()
            print('Error code: ', e.code, ErrorInfo)
            sys.exit()
        except  urllib.error.URLError as e:
            ErrorInfo = e.read().decode()
            print('Error code: ', e.code, ErrorInfo)
            sys.exit()
        json_data = json.loads(data)
        print('completed')

        df = pd.DataFrame()
        for i in json_data['days']:
            for j in i['hours']:
                j['datetime'] = i['datetime'] + ' ' + j['datetime']
                df_j = pd.DataFrame([j])
                df = pd.concat([df, df_j])

        df = df.reset_index()
        df = df.drop(columns=['index'])
        df = df[['datetime', 'temp', 'humidity', 'windspeed', 'winddir', 'cloudcover', 'visibility', 'conditions']]

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

        # data formatting
        df['conditions'] = df['conditions'].apply(np.int64)
        df['datetime'] = pd.to_datetime(df['datetime'])

        # Inference:
        time_idx = df[df['datetime'] == End_date + ' ' + '07:00:00'].index[0]
        self.to_inf = df.iloc[time_idx-12:time_idx]

        # To SQL
        self.to_sql = df.iloc[0:time_idx]
        self.to_sql['datetime'] = self.to_sql['datetime'].astype('str')
        self.to_sql.to_sql(con=self.db, name='stuttgart_weather', if_exists='append', index=False)

    def _load_model(self):
        # Loading a model from MLflow runs
        model_version = 2

        model = mlflow.pyfunc.load_model(
            model_uri=f"mlruns/{model_version}/7214477162f54ac1859d4cfb199ac41f/artifacts"
        )

        return model

    def evaluate(self):
        # Evaluating predicted values on historical data
        current_date = datetime.datetime.now()
        threshold = 1

        start_date = current_date - datetime.timedelta(days=threshold)
        end_date = current_date
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')

        historical_data = self.connector.get_data_alch(self.db, 'stuttgart_weather')
        predicted_data = self.connector.get_data_alch(self.db, 'prediction')

        filtered_historical = historical_data[historical_data.datetime.between(start_date, end_date)]
        filtered_predicted = predicted_data[predicted_data.datetime.between(start_date, end_date)]

        # Filter for unique timestamps
        filtered_historical = filtered_historical.drop_duplicates(subset='datetime', keep='first')
        filtered_predicted = filtered_predicted.drop_duplicates(subset='datetime', keep='first')

        df_merge = pd.merge(filtered_historical, filtered_predicted, on='datetime')

        acc = accuracy_score(df_merge['conditions'], df_merge['prediction'], normalize=True)

        print('Real-time model accuracy in date range from: {0} to {1} is:'.format(start_date, end_date))
        print(f'{round(acc*100,1)} %')

        eval_df = pd.DataFrame(data=[{'datetime':end_date, 'accuracy':acc*100}])

        eval_df.to_sql(con=self.db, name='evaluation', if_exists='append', index=False)
        print('evaluation record stored successfully')

    def sms(self, prediction_df):
        # Sends an SMS with the weather update
        coat_list = []
        coat_hours = prediction_df[prediction_df['prediction'] != 0]
        if not coat_hours.empty:
            for i in coat_hours['datetime']:
                coat_list.append(i.strftime('%H:%M'))

        date = prediction_df.datetime[0].strftime('%Y-%m-%d')

        if coat_list:
            msg = 'Today is: {0}\nExpected rainy hours in Stuttgart are: {1}\nPlease pick up the coat!'.format(date, coat_list)
        else:
            msg = 'Today is: {0}\nNo rain is expected!'.format(date)

        self.sms_send(msg)

    def sms_send(self, msg):
        account_sid = os.environ['API_TWILIO_SID']
        auth_token = os.environ['API_TWILIO_TOKEN']
        tel_num = os.environ['API_TWILIO_NUM']

        client = Client(account_sid, auth_token)

        client.messages.create(
            body= msg,
            from_= '+18123988103',
            to= tel_num
        )

        return True

    def run(self):
      # Inference
      self.post_analysis = copy.copy(self.to_inf)
      date_strf = self.post_analysis.iloc[-1]['datetime'].strftime('%Y-%m-%d %H:%M:%S')
      date_from = datetime.datetime.strptime(date_strf, '%Y-%m-%d %H:%M:%S')
      prediction_df = pd.DataFrame(columns=['datetime', 'prediction'])

      hour_list = []
      for hour in range(12):
          date_hour = date_from + datetime.timedelta(hours=hour + 1)
          hour_list.append(date_hour)

      prediction_df['datetime'] = hour_list

      self.to_inf = self.to_inf.drop(columns=['datetime'])

      prediction = self.model.predict(self.to_inf)

      # Prediction for the next 12 hours
      prediction_df['prediction'] = prediction

      # Store prediction
      prediction_df.to_sql(con=self.db, name='prediction', if_exists='append', index=False)
      print('record saved successfully')

      self.evaluate()
      self.sms(prediction_df)

if __name__ == '__main__':
    Inference()