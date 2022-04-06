import connexion
from connexion import NoContent

import datetime, requests, json, yaml, os, os.path, sqlite3

from os.path import exists
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from stats import Stats

import logging
from logging import config

from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS, cross_origin

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

if not os.path.exists(app_config["datastore"]["filename"]):
    """ Creates the sqlite database tables """
    conn = sqlite3.connect(app_config["datastore"]["filename"])

    c = conn.cursor()

    c.execute('''
            CREATE TABLE stats
            (id INTEGER PRIMARY KEY ASC,
            num_bs_readings INTEGER NOT NULL,
            max_bs_readings INTEGER,
            min_bs_readings INTEGER,
            num_cl_readings INTEGER NOT NULL,
            max_cl_readings INTEGER,
            min_cl_readings INTEGER,
            last_updated VARCHAR(100) NOT NULL)
            ''')

    conn.commit()
    conn.close()

DB_ENGINE = create_engine("sqlite:///%s" % app_config["datastore"]["filename"])
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()


def query_stats():
    session = DB_SESSION()
    readings = session.query(Stats).order_by(Stats.last_updated.desc()).first()
    session.close()

    if readings is None:
        readings = {
            "num_bs_readings": 0,
            "max_bs_readings": 0,
            "min_bs_readings": 99999,
            "num_cl_readings": 0,
            "max_cl_readings": 0,
            "min_cl_readings": 99999,
            "last_updated": "2016-08-29T09:12:33Z"
        }
    else:
        readings = readings.to_dict()

    return readings


def populate_stats():
    logger.info("Start Periodic Processing")
    stats = query_stats()
    last_updated = stats['last_updated']
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    stats["last_updated"] = timestamp

    bs_readings = get_events("blood_sugar_reading", last_updated, timestamp)

    print(bs_readings)
    print(stats)
    stats["num_bs_readings"] += len(bs_readings)
    for result in bs_readings:
        if result["bs_requests"] > stats["max_bs_readings"]:
            stats["max_bs_readings"] = result["bs_requests"]
        if result["bs_requests"] < stats["min_bs_readings"]:
            stats["min_bs_readings"] = result["bs_requests"]
        logger.debug("The blood sugar request, ID: {}, has been processed".format(result["trace_id"]))

    cl_readings = get_events("cortisol_level_reading", last_updated, timestamp)

    print(cl_readings)

    stats["num_cl_readings"] += len(cl_readings)
    for result in cl_readings:
        if result["cl_requests"] > stats["max_cl_readings"]:
            stats["max_cl_readings"] = result["cl_requests"]
        if result["cl_requests"] < stats["min_cl_readings"]:
            stats["min_cl_readings"] = result["cl_requests"]
        logger.debug("The cortisol level requests, ID: {}, has been processed".format(result["trace_id"]))

    write_stats(stats)
    logger.info("End Periodic Processing")


def get_events(event_type, start_timestamp, end_timestamp):
    url = app_config["assign_{}".format(event_type)]["url"]
    res = requests.get(url, params={"start_timestamp": start_timestamp, "end_timestamp": end_timestamp})
    res_dict = json.loads(res.text)
    logger.info("Readings {} events received: {}".format(event_type, len(res_dict)))

    if res.status_code != 200:
        logger.error("Response code: {}".format(res.status_code))

    return res_dict


def write_stats(stats):
    session = DB_SESSION()
    stats = Stats(
        stats["num_bs_readings"],
        stats["max_bs_readings"],
        stats["min_bs_readings"],
        stats["num_cl_readings"],
        stats["max_cl_readings"],
        stats["min_cl_readings"],
        datetime.datetime.strptime(stats["last_updated"], "%Y-%m-%dT%H:%M:%SZ")
    )

    session.add(stats)
    session.commit()
    session.close()


def get_stats():
    logger.info("GET request for stats started")

    session = DB_SESSION()
    stats = session.query(Stats).order_by(Stats.last_updated.desc()).first()
    session.close()

    if stats is None:
        logger.error("404")
    else:
        stats = stats.to_dict()

    logger.debug(stats)
    logger.info("GET request completed")

    return stats, 200


app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml",
            base_path="/processing",
            strict_validation=True,
            validate_responses=True)

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, use_reloader=False)