import numpy as np
from config_db.connector import Connector
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import RandomizedSearchCV
import mlflow
import datetime
import warnings
with warnings.catch_warnings():
    warnings.simplefilter(action='ignore', category=FutureWarning)

class CoatTrain():
    def __init__(self):
        self.connector = Connector('./config_db/config_mysql.yaml', 'coat_project_local', 'alchemy')
        self.db = self.connector.connect()

        df_raw = self._load_data()
        df_preprocessed = self._data_preprocess(df_raw)

        self.train(df_preprocessed)

    def _load_data(self):
        # Loads data from the database
        return self.connector.get_data_alch(self.db, 'stuttgart_weather')

    def _data_preprocess(self, df):
        # Pre-process loaded data

        # Shifting the data 12 hours ahead
        df['future_weather_condition'] = df.conditions.shift(12, axis=0)
        df = df.dropna()

        df['conditions'] = df['conditions'].apply(np.int64)
        df['future_weather_condition'] = df['future_weather_condition'].apply(np.int64)

        return df

    def train(self, df):
        # Trains the model
        y = df['future_weather_condition']
        X = df.drop(columns=['future_weather_condition', 'datetime'])

        # Allocating 30% of data for validation
        test_size = int(round(len(X) - (len(X) * 0.3), 1))

        X_train = X[:test_size]
        y_train = y[:test_size]

        X_test = X[test_size:]
        y_test = y[test_size:]

        # Train test split for training
        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=1)

        set_name = 'Stuttgart_' + str(datetime.datetime.now().strftime('%Y-%d-%Y'))

        # Standard scaling the values
        sc = StandardScaler()
        X_train = sc.fit_transform(X_train)
        X_test = sc.transform(X_test)

        print('Searching for best grid params')
        # Random Forest Classifier grid-search
        params = {'n_estimators': [5, 10, 12, 15, 17, 20, 30],
                  'max_depth':[100, 200, 300, 400, 500, 600, 700, 800],
                  'min_samples_split':[2, 5, 10],
                  'min_samples_leaf':[1, 2, 4],
                  'bootstrap':[True, False]}

        rf_base = RandomForestClassifier()

        rf_grid = RandomizedSearchCV(rf_base, params)
        rf_grid.fit(X_train, y_train)
        clf = RandomForestClassifier(**rf_grid.best_params_)

        mlflow.set_experiment('randomforest-grid')
        with mlflow.start_run() as run:
            print('Training...')
            mlflow.log_param('dataset_name ', set_name)
            mlflow.log_param('dataset_size ', X_train.size)

            clf.fit(X_train, y_train)
            predict = clf.predict(X_val)
            predict_test = clf.predict(X_test)

            for i in clf.get_params(deep=True):
                mlflow.log_param(i, clf.get_params(deep=True)[i])

            acc = accuracy_score(y_val, predict, normalize=True)
            fscore = f1_score(y_val, predict, average="macro")
            precision = precision_score(y_val, predict, average="macro")
            recall = recall_score(y_val, predict, average="macro")

            acc_test = accuracy_score(y_test, predict_test, normalize=True)
            fscore_test = f1_score(y_test, predict_test, average="macro")
            precision_test = precision_score(y_test, predict_test, average="macro")
            recall_test = recall_score(y_test, predict_test, average="macro")


            mlflow.log_metric('train_acc ', acc)
            mlflow.log_metric('train_fscore', fscore)
            mlflow.log_metric('train_precision', precision)
            mlflow.log_metric('train_recall', recall)

            mlflow.log_metric('test_acc ', acc_test)
            mlflow.log_metric('test_fscore', fscore_test)
            mlflow.log_metric('test_precision', precision_test)
            mlflow.log_metric('test_recall', recall_test)

            mlflow.sklearn.save_model(clf, 'mlruns/2/' + run.info.run_id + '/artifacts/')

        mlflow.end_run()

        pass

CoatTrain()