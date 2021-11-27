import connexion
from connexion import NoContent
from flask import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
import datetime, yaml, logging, logging.config, json, time, os
from blood_sugar import BloodSugar
from cortisol_level import CortisolLevel
import mysql.connector
from pykafka.common import OffsetType
from threading import Thread
from pykafka import KafkaClient
from sqlalchemy import and_
#pip install swagger-ui-bundle
#pip install mysql-connector-python
#pip install kafka-python
#pip install pykafka


# with open('log_conf.yml', 'r') as f: 
#     log_config = yaml.safe_load(f.read())
#     logging.config.dictConfig(log_config)

# logger = logging.getLogger('basicLogger')

# with open('app_conf.yml', 'r') as f: 
#     app_config = yaml.safe_load(f.read())
#     host = app_config["datastore"]["hostname"]
#     logger.info(f"Connecting to DB. Hostname {host}, Port: 3306")

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"
    
with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file) 
logger.info("Log Conf File: %s" % log_conf_file)

DB_ENGINE = create_engine(f'mysql+pymysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@{app_config["datastore"]["hostname"]}:{app_config["datastore"]["port"]}/{app_config["datastore"]["db"]}')
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def get_blood_sugar_reading(start_timestamp, end_timestamp):
    "Gets new instore_sales event data after timestamp"
    session=DB_SESSION()
    # timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ") 
    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ") # Storage Service endpoints before only take a single timestamp, so the Processing won't know the end time 9*3
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ") # Storage Service endpoints before only take a single timestamp, so the Processing won't know the end time 9*3
    # transactions= session.query(InstoreSales).filter(InstoreSales.date_created >= timestamp_datetime)
    transactions = session.query(BloodSugar).filter( and_(BloodSugar.date_created >= start_timestamp_datetime, BloodSugar.date_created < end_timestamp_datetime))
    trans_list = []
    for tran in transactions:
        trans_list.append(tran.to_dict())
    session.close()

    logger.info("Query for Blood Sugar after %s returns %d results" %(start_timestamp, len(trans_list)))
    
    return trans_list, 200  

def get_cortisol_level_reading(start_timestamp, end_timestamp):
    "Gets new instore_sales event data after timestamp"
    session=DB_SESSION()
    # timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ") # Storage Service endpoints before only take a single timestamp, so the Processing won't know the end time 9*3
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ") # Storage Service endpoints before only take a single timestamp, so the Processing won't know the end time 9*3
    # transactions= session.query(OnlineSales).filter(OnlineSales.date_created >= timestamp_datetime)
    transactions = session.query(CortisolLevel).filter( and_(CortisolLevel.date_created >= start_timestamp_datetime, CortisolLevel.date_created < end_timestamp_datetime))
    trans_list = []
    for tran in transactions:
        trans_list.append(tran.to_dict())
    session.close()

    logger.info("Query for Cortisol Levels after %s returns %d results" %(start_timestamp, len(trans_list)))
    
    return trans_list, 200


def report_blood_sugar_reading(body):
    """ Receives a blood sugar reading """

    session = DB_SESSION()

    bs = BloodSugar(body['patient_id'],
                    body['device_id'],
                    body['timestamp'],
                    body['blood_sugar'])

    session.add(bs)
    unq_id = body["patient_id"]

    logger.debug(f"Stored event Blood Sugar request with a unique id of {unq_id}")

    session.commit()
    session.close()

    #//return NoContent, 201 #Remove the previous POST API endpoints as new events will now be received through messages from Kafka.
    

def report_cortisol_level_reading(body):
    """ Receives a cortisol level reading """

    session = DB_SESSION()

    cl = CortisolLevel(body['patient_id'],
                        body['device_id'],
                        body['timestamp'],
                        body['cortisol_level'])

    unq_id = body["patient_id"]
    session.add(cl)

    logger.debug(f"Stored event Blood Sugar request with a unique id of {unq_id}")

    session.commit()
    session.close()
    #//return NoContent, 201 #Remove the  POST API endpoints as new events will now be received through messages from Kafka.

def process_messages():
    """ Process event messages """
    hostname = "%s:%d" % (app_config["events"]["hostname"],
                        app_config["events"]["port"]) 
    # client = KafkaClient(hosts=hostname)
    # topic = client.topics[str.encode(app_config["events"]["topic"])]

    max_retry =app_config["connecting_kafka"]["retry_count_max"]
    retry_count = 0
    while retry_count < max_retry:
        logger.info(f"Connecting to Kafka and the current retry count is {retry_count + 1}")
        try:
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config["events"]["topic"])]
            logger.info("CONNECTED TO KAFKA SUCCESSULLY")
            retry_count = max_retry
        except:
            logger.error("Cannot Connect to Kafka. The connection failed")
            time.sleep(app_config["connecting_kafka"]["time_sleep"])
            retry_count += 1


    # Create a consume on a consumer group, that only reads new messages \
    # (uncommitted messages) when the service re-starts (i.e., it doesn't 
    # read all the old messages from the history in the message queue). 
    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                            reset_offset_on_start=False, 
                                            auto_offset_reset=OffsetType.LATEST)
    
    # This is blocking - it will wait for a new message
    for msg in consumer:
        try:
            msg_str = msg.value.decode('utf-8') 
            msg = json.loads(msg_str) 
            logger.info("Message: %s" % msg)

            payload = msg["payload"]

            if msg["type"] == "blood-sugar": #Change this to your event type - Get this from the openapi.yml line 13 `/sales/instore` so event type is `instore`
                # Store the event1 (i.e., the payload) to the DB
                report_blood_sugar_reading(payload)
                
            elif msg["type"] == "cortisol-level": # Change this to your event type 
                #Store the event2 (i.e., the payload) to the DB
                report_cortisol_level_reading(payload)

            # Commit the new message as being read
            consumer.commit_offsets()
        except:
            logger.error("Something is wrong. Cannot Store in DB table")

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", 
            strict_validation=True, 
            validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages) 
    t1.setDaemon(True)
    t1.start()

    app.run(port=8090)