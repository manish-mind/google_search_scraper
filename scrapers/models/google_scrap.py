from sqlalchemy import Column, Integer, String,Float,Boolean,ForeignKey,Text
from sqlalchemy.dialects.postgresql import JSONB

from scrapers.db.session import Base,TimestampMixin
from sqlalchemy.orm import relationship

class SearchSession(Base,TimestampMixin):
    __tablename__ = "search_session"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    search_name = Column(String, nullable=False)
    about=Column(Text,nullable=True)
    about_info=Column(JSONB,nullable=True)

    results = relationship("SearchResult", back_populates="session")
    sponsored = relationship("SponsoredOnPage", back_populates="session")
    products = relationship("ProductsOnPage", back_populates="session")

class SearchResult(Base,TimestampMixin):
    __tablename__="search_result"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title =  Column(String,nullable=True)
    subtitle = Column(String,nullable=True)
    heading = Column(String,nullable=True)
    description = Column(String,nullable=True)
    is_sponsored = Column(Boolean, nullable=True)
    page_no=Column(Integer,nullable=True)
    session_id = Column(Integer, ForeignKey("search_session.id"))
    session = relationship("SearchSession", back_populates="results")

class ProductsOnPage(Base,TimestampMixin):
    __tablename__="products_on_page"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_title= Column(String,nullable=True)
    product_price=Column(String,nullable=True)
    product_deliver_by= Column(String,nullable=True)
    product_image=Column(String,nullable=True)

    session_id = Column(Integer, ForeignKey("search_session.id"))
    session = relationship("SearchSession", back_populates="products")

class SponsoredOnPage(Base,TimestampMixin):
    __tablename__="sponsored_on_page"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sponsored_title= Column(String,nullable=True)
    sponsored_subtitle= Column(String,nullable=True)
    sponsored_heading= Column(String,nullable=True)
    sponsored_description=Column(String,nullable=True)

    session_id = Column(Integer, ForeignKey("search_session.id"))
    session = relationship("SearchSession", back_populates="sponsored")
