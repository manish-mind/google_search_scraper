from sqlalchemy import Column, Integer, String
from scrapers.db.session import Base,TimestampMixin


class SearchResult(Base,TimestampMixin):
    __tablename__="search_result"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String,nullable=True)
    subtitle = Column(String,nullable=True)
    heading = Column(String,nullable=True)
    description = Column(String,nullable=True)