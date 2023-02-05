from config_db.connector import Connector
import matplotlib.pyplot as plt

def plot_eval(eval_data):
    eval_data = eval_data.drop_duplicates(subset='datetime', keep='first')

    plt.plot(eval_data['datetime'], eval_data['accuracy'], marker='o')
    plt.show()

if __name__ == '__main__':
    connector = Connector('config_db/' + 'config_mysql.yaml', 'coat_project_local', 'alchemy')
    db = connector.connect()
    eval_data = connector.get_data_alch(db, 'evaluation')
    plot_eval(eval_data)
    print('z')