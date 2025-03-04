"""Plugin model for storing plugin information."""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from qorzen.models.base import Base, TimestampMixin


class Plugin(Base, TimestampMixin):
    """Plugin model for storing plugin metadata and configuration."""

    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    version = Column(String(32), nullable=False)
    description = Column(String(255), nullable=True)
    author = Column(String(128), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    installed_path = Column(String(255), nullable=True)
    configuration = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Plugin(id={self.id}, name='{self.name}', version='{self.version}')>"
