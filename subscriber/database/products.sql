-- This script create the products table

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL,
    page INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    seller TEXT NOT NULL,
    current_price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    discount_percentage TEXT,
    currency TEXT NOT NULL,
    rating DECIMAL(3, 1),
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
    updated_at_audit TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);