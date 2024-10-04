from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db.base import Base


class OzonCampaigns(Base):
    __tablename__ = "ozon_campaigns"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    state = Column(String(50))
    from_date = Column(DateTime)
    to_date = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # Связь с таблицей ozon_campaigns_products
    products = relationship(
        "OzonCampaignsProducts", back_populates="campaign", cascade="all, delete-orphan"
    )


class OzonCampaignsProducts(Base):
    __tablename__ = "ozon_campaigns_products"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(
        Integer, ForeignKey("ozon_campaigns.campaign_id"), nullable=False
    )
    product_id = Column(Integer, nullable=False)

    # Связь с таблицей ozon_campaigns
    campaign = relationship("OzonCampaigns", back_populates="products")
    # Уникальный ключ по нескольким полям
    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "product_id", name="unique_campaign_id_product_id"
        ),
    )
