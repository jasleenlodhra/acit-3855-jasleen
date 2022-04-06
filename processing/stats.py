from sqlalchemy import Column, Integer, DateTime
from base import Base

class Stats(Base):

    __tablename__ = "stats"

    id = Column(Integer, primary_key=True)
    num_bs_readings = Column(Integer, nullable=False)
    max_bs_readings = Column(Integer, nullable=True)
    min_bs_readings = Column(Integer, nullable=True)
    num_cl_readings = Column(Integer, nullable=False)
    max_cl_readings = Column(Integer, nullable=True)
    min_cl_readings = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=False)

    def __init__(self, num_bs_readings, max_bs_readings, min_bs_readings, num_cl_readings, max_cl_readings, min_cl_readings, last_updated):

        self.num_bs_readings = num_bs_readings
        self.max_bs_readings = max_bs_readings
        self.min_bs_readings = min_bs_readings
        self.num_cl_readings = num_cl_readings
        self.max_cl_readings = max_cl_readings
        self.min_cl_readings = min_cl_readings
        self.last_updated = last_updated

    def to_dict(self):

        dict = {}
        dict['num_bs_readings'] = self.num_bs_readings
        dict['max_bs_readings'] = self.max_pu_count
        dict['min_bs_readings'] = self.min_bs_readings
        dict['num_cl_readings'] = self.num_cl_readings
        dict['max_cl_readings'] = self.max_cl_readings
        dict['min_cl_readings'] = self.min_cl_readings
        dict['last_updated'] = self.last_updated.strftime("%Y-%m-%dT%H:%M:%SZ")

        return dict