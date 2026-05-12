from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from backend.db import Base


class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=True)
    url = Column(String, nullable=True)
    verdict = Column(String, nullable=False)
    level = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)
    probability = Column(Float, nullable=False)
    raw_features = Column(JSON, nullable=True)
    reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    explanations = relationship("Explanation", back_populates="scan", cascade="all, delete-orphan")


class Explanation(Base):
    __tablename__ = "explanations"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    feature = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    direction = Column(String, nullable=True)
    value = Column(Float, nullable=True)

    scan = relationship("Scan", back_populates="explanations")
