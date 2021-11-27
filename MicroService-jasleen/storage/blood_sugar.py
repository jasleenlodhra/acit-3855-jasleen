from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


class BloodSugar(Base):
    """ Blood Sugar """

    __tablename__ = "blood_sugar"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String(250), nullable=False)
    device_id = Column(String(250), nullable=False)
    timestamp = Column(String(100), nullable=False)
    blood_sugar = Column(Integer, nullable=False)
    date_created = Column(DateTime, nullable=False)

    def __init__(self, patient_id, device_id, timestamp, blood_sugar):
        """ Initializes a blood sugar reading """
        self.patient_id = patient_id
        self.device_id = device_id
        self.blood_sugar = blood_sugar
        self.timestamp = timestamp
        self.date_created = datetime.datetime.now() # Sets the date/time record is created

    def to_dict(self):
        """ Dictionary Representation of a blood sugar reading """
        dict = {}
        dict['id'] = self.id
        dict['patient_id'] = self.patient_id
        dict['device_id'] = self.device_id
        dict['blood_sugar'] = self.blood_sugar
        dict['timestamp'] = self.timestamp
        dict['date_created'] = self.date_created

        return dict