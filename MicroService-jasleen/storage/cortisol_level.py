from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


class CortisolLevel(Base):
    """ Cortisol Level """

    __tablename__ = "cortisol_level"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String(250), nullable=False)
    device_id = Column(String(250), nullable=False)
    timestamp = Column(String(100), nullable=False)
    date_created = Column(DateTime, nullable=False)
    cortisol_level = Column(Integer, nullable=False)

    def __init__(self, patient_id, device_id, timestamp, cortisol_level):
        """ Initializes a cortisol level reading """
        self.patient_id = patient_id
        self.device_id = device_id
        self.timestamp = timestamp
        self.date_created = datetime.datetime.now() # Sets the date/time record is created
        self.cortisol_level = cortisol_level

    def to_dict(self):
        """ Dictionary Representation of a cortisol level reading """
        dict = {}
        dict['id'] = self.id
        dict['patient_id'] = self.patient_id
        dict['device_id'] = self.device_id
        dict['cortisol_level'] = self.cortisol_level
        dict['timestamp'] = self.timestamp
        dict['date_created'] = self.date_created

        return dict
