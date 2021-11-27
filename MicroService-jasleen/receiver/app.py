import connexion
from connexion import NoContent
import json, logging.config, requests, logging, yaml, time
import os
import uuid
from flask import Response
from pykafka import KafkaClient
from datetime import datetime
import datetime


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

hostname = "%s:%d" % (app_config["events"]["hostname"],
                    app_config["events"]["port"]) 
max_retry =app_config["connecting_kafka"]["retry_count_max"]
retry_count = 0
while retry_count < max_retry:
    logger.info(f"Connecting to Kafka and the current retry count is {retry_count + 1}")
    try:
        client = KafkaClient(hosts= hostname)
        topic = client.topics[str.encode(app_config["events"]["topic"])]
        producer = topic.get_sync_producer()
        retry_count = max_retry
    except:
        logger.error("Cannot Connect to Kafka. The connection failed")
        time.sleep(app_config["connecting_kafka"]["time_sleep"])
        retry_count += 1

def report_blood_sugar_reading(body):
    logger.info(f"Received event report_blood_sugar_reading request with a unique id of {body['patient_id']}")

    producer = topic.get_sync_producer()

    msg = {"type": "blood-sugar",
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "payload": body}
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    
    return msg_str, 201 #! You will need to hard-code your status code to 201 since you will no longer get it from the response of the requests.post call


def report_cortisol_level_reading(body):
    logger.info(f"Received event report_cortisol_level_reading request with a unique id of {body['patient_id']}")
    producer = topic.get_sync_producer()

    msg = {"type": "cortisol-level",
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "payload": body}
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    return msg_str, 201 #! You will need to hard-code your status code to 201 since you will no longer get it from the response of the requests.post call

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", 
            strict_validation=True, 
            validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080)
