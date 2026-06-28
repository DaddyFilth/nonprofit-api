import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./nonprofit.db",
        description="Database connection URL"
    )
    
    # Email Configuration
    email_provider: str = Field(
        default="smtp",
        description="Email provider: smtp, gmail, sendgrid"
    )
    smtp_host: Optional[str] = Field(default=None, description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    
    # Gmail API
    gmail_client_id: Optional[str] = Field(default=None, description="Gmail OAuth client ID")
    gmail_client_secret: Optional[str] = Field(default=None, description="Gmail OAuth client secret")
    gmail_refresh_token: Optional[str] = Field(default=None, description="Gmail OAuth refresh token")
    
    # SendGrid
    sendgrid_api_key: Optional[str] = Field(default=None, description="SendGrid API key")
    
    # Search API
    search_provider: str = Field(
        default="serpapi",
        description="Search provider: serpapi, google_custom_search, scrape"
    )
    serpapi_key: Optional[str] = Field(default=None, description="SerpApi API key")
    google_search_api_key: Optional[str] = Field(default=None, description="Google Custom Search API key")
    google_search_engine_id: Optional[str] = Field(default=None, description="Google Custom Search Engine ID")
    
    # LLM Configuration
    llm_provider: str = Field(
        default="openai",
        description="LLM provider: openai, anthropic, gemini"
    )
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    
    # Bot Configuration
    bot_email: str = Field(default="procurement@nonprofit.org", description="Bot email address")
    bot_name: str = Field(default="Material Procurement Bot", description="Bot name")
    organization_name: str = Field(default="Our Nonprofit", description="Organization name")
    
    # Organization Identity
    organization_mission: str = Field(
        default="community-driven initiative providing essential exterior home repair, property restoration, and maintenance for elderly and low-income families at absolutely no cost",
        description="Organization mission statement"
    )
    organization_location: str = Field(
        default="Lawton, Oklahoma",
        description="Organization location"
    )
    organization_operating_names: str = Field(
        default="Lawton Community Restoration Initiative",
        description="Operating names/brands"
    )
    
    # Contact Information
    contact_name: str = Field(default="Michael Yessian", description="Contact person name")
    reply_to_email: str = Field(default="shinelikeacrime@gmail.com", description="Reply-to email address")
    contact_phone: str = Field(default="405-204-1427", description="Contact phone number")
    contact_phone_note: str = Field(default="Text communication only", description="Phone usage note")
    
    # Rate Limiting
    max_emails_per_hour: int = Field(default=20, description="Maximum emails to send per hour")
    max_searches_per_hour: int = Field(default=30, description="Maximum searches per hour")
    delay_between_emails: int = Field(default=60, description="Delay between emails in seconds")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="procurement_bot.log", description="Log file path")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()