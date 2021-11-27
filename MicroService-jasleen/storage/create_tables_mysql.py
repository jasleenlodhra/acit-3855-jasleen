import mysql.connector
import yaml
#pip install mysql-connector-python

with open('app_conf.yml', 'r') as f: 
    app_config = yaml.safe_load(f.read())

db_conn = mysql.connector.connect(host= app_config["datastore"]["hostname"],
                                    port= app_config["datastore"]["port"], 
                                    user= app_config["datastore"]["user"], 
                                    password= app_config["datastore"]["password"])
db_cursor = db_conn.cursor()

db_name= app_config["datastore"]["db"]
db_cursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(db_name) )

db_cursor.execute('''
    CREATE TABLE events.blood_sugar
    (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
    patient_id VARCHAR(250) NOT NULL,
    device_id VARCHAR(250) NOT NULL,
    timestamp VARCHAR(100) NOT NULL,
    blood_sugar INTEGER NOT NULL,
    date_created VARCHAR(100) NOT NULL)
    ''')

db_cursor.execute('''
    CREATE TABLE events.cortisol_level
    (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
    patient_id VARCHAR(250) NOT NULL,
    device_id VARCHAR(250) NOT NULL,
    timestamp VARCHAR(100) NOT NULL,
    cortisol_level INTEGER NOT NULL,
    date_created VARCHAR(100) NOT NULL)
    ''')
    
db_conn.commit()
db_conn.close()