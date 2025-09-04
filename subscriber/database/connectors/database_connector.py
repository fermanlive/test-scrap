# Database connector for Supabase (Postgres)

import os
from pathlib import Path
from dataclasses import asdict
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv
from typing import List
from scraper.models.models import Product
from loguru import logger

load_dotenv()

class DatabaseConnector:
    """Database connector for Supabase (Postgres)"""

    def __init__(self):
        try:
            self.supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
                )
        except Exception as e:
            logger.error(f"Error initializing database connector: {e}")
            raise e
        logger.info("Database connector initialized")
    
    def insert_products(self, products: List[Product]):
        """Insert products into the database."""
        logger.info(f"Inserting {len(products)} products into the database")
        for product in products:
            try:
                logger.debug(f"Inserting product {product.title} into the database")
                logger.debug(f"Product: {asdict(product)}")
                self.supabase.table("products").insert(self._map_product(product)).execute()
            except Exception as e:
                logger.error(f"Error inserting product {product.title} into the database: {e}")
                continue
        logger.info(f"Products inserted into the database")
        return True

    def _map_product(self, product: Product) -> dict:
        """Map product to dictionary.
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            seller TEXT NOT NULL,
            current_price DECIMAL(10, 2) NOT NULL,
            original_price DECIMAL(10, 2),
            discount_percentage TEXT,
            currency TEXT NOT NULL,
            rating DECIMAL(2, 2),
            review_count INT,
            stock_quantity TEXT,
            features JSONB NOT NULL DEFAULT '{}'::jsonb,
            images JSONB NOT NULL DEFAULT '{}'::jsonb,
            description TEXT,
            seller_location TEXT,
            shipping_method TEXT,
            brand TEXT,
            scraped_at TIMESTAMP NOT NULL,
            created_at_audit TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at_audit TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            category TEXT NOT NULL,
            page INTEGER NOT NULL
        """
        return {
            "title": product.title,
            "url": product.url,
            "seller": product.seller,
            "current_price": float(product.current_price) if product.current_price else None,
            "original_price": float(product.original_price) if product.original_price else None,
            "discount_percentage": product.discount_percentage,
            "currency": product.currency,
            "rating": float(product.rating) if product.rating else None,
            "review_count": product.review_count,
            "stock_quantity": product.stock_quantity,
            "features": product.features,
            "images": product.images,
            "description": getattr(product, 'description', None),
            "seller_location": product.seller_location,
            "shipping_method": getattr(product, 'shipping_method', None),
            "brand": product.brand,
            "scraped_at": product.scraped_at.isoformat() if product.scraped_at else None,
            "created_at_audit": datetime.now().isoformat(),
            "updated_at_audit": datetime.now().isoformat(),
            "category": product.category,
            "page": product.page
        }

    def get_products(self) -> List[Product]:
        """Get products from the database."""
        logger.info(f"Getting products from the database")
        try:
            products = self.supabase.table("products").select("*").execute()
        except Exception as e:
            logger.error(f"Error getting products from the database: {e}")
            raise e
        logger.info(f"Products got from the database")
        return products 
            
    def get_product(self, id: str) -> Product:
        """Get a product from the database."""
        logger.info(f"Getting product {id} from the database")
        try:
            product = self.supabase.table("products").select("*").eq("id", id).execute()
        except Exception as e:
            logger.error(f"Error getting product {id} from the database: {e}")
            raise e
        logger.info(f"Product {id} got from the database")
        return product