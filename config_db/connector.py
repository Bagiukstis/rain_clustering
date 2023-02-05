import pandas as pd
import mysql.connector
import yaml
import ssl
from sqlalchemy import create_engine, select, Table, MetaData
import os

class Connector():
    def __init__(self, config, database_key, mode) -> None:
        self.mode = mode
        #self.mode = 'alchemy'
        self.database_key = database_key

        # Without kubes
        # self.config = self.yml_parser(config)
        # self.config = self.config[database_key]

        # Using kubes secrets
        self.config = {'USER': os.environ["SQL_SERVER_USERNAME"],
                       'PASSWORD': os.environ["SQL_SERVER_PASSWORD"],
                       'HOST': os.environ["SQL_SERVER_HOST"],
                       'DATABASE': os.environ["SQL_SERVER_DATABASE"],
                       'PORT': os.environ["SQL_SERVER_PORT"]}

    def yml_parser(self, config):
        with open(config, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    def connect(self):
        if self.mode != 'alchemy':
            cnx = mysql.connector.connect(user=self.config['USER'], password=self.config['PASSWORD'],
                                          host=self.config['HOST'], database=self.config['DATABASE'], port=self.config["PORT"])

            cnx._ssl['version'] = ssl.PROTOCOL_TLSv1_2
        else:
            # cnx = create_engine(
            #     "mysql+pymysql://" + self.config['USER'] + ":" + self.config['PASSWORD'] + "@" + self.config['HOST'] + ":" + self.config['PORT'] + "/" + self.config['DATABASE'])

            cnx = create_engine(
                f"mysql+pymysql://{self.config['USER']}:{self.config['PASSWORD']}@{self.config['HOST']}:{self.config['PORT']}/{self.config['DATABASE']}")
        return cnx

    def get_data(self, db, table_name):
        cursor = db.cursor()
        cursor.execute('SELECT * FROM '+ self.config['DATABASE'] + '.'+ table_name)
        field_names = [i[0] for i in cursor.description]
        df = pd.DataFrame(cursor.fetchall())
        df.columns = field_names
        return df

    def get_data_alch(self, db, table_name):
        # Get data with the alchemy package
        metadata = MetaData()
        table_data = Table(table_name, metadata, autoload=True, autoload_with=db)
        query = select([table_data])
        results = db.execute(query).fetchall()
        return pd.DataFrame(results)

    def insert_data(self, db, table_name, values):

        cursor = db.cursor()
        sql = 'INSERT INTO ' + self.config['DATABASE'] + '.' + table_name + '(datetime, temp, humidity, windspeed, winddir, cloudcover, visibility, conditions) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'


        if any(isinstance(i, list) for i in values) == False:
            try:
                cursor.execute(sql, tuple(values))
            except mysql.connector.errors.IntegrityError:
                db.rollback()
        else:
            for i in values:
                cursor.execute(sql, tuple(i))

        db.commit()
        print('record inserted')