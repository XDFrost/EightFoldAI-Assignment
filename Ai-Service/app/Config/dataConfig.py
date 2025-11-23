from dataclasses import dataclass, field
from dotenv import load_dotenv
from typing import List
import os
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

class Config:
    """
    Contains configuration settings for whole project.
    """
    @dataclass(frozen=True)
    class MainAppConfig:
        """
            Main file config
        """
        TITLE: str = "SalesBot App"
        VERSION: str = "1.0.0"
        
        ALLOWORIGINS: List[str] = field(default_factory=lambda: ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"])
        ALLOWCREDENTIALS: bool = True
        ALLOWMETHODS: List[str] = field(default_factory=lambda: ["*"])
        ALLOWHEADERS: List[str] = field(default_factory=lambda: ["*"])
        
        SOCKETCHATPREFIX: str = "/ai-service/ws"
    
    @dataclass(frozen=True)
    class UvicornConfig:
        """
            Uvicorn config
        """
        APP: str = "app.main:app"
        HOST: str = "0.0.0.0"
        PORT: int = 8000
        RELOAD: bool = True
        
    @dataclass(frozen=True)
    class Config:
        """
            Main Config for ai-service
        """
        GOOGLE_API_KEY: str
        SUPABASE_URL: str
        SUPABASE_KEY: str
        TAVILY_API_KEY: str
        PERPLEXITY_API_KEY: str
        DATABASE_URL: str
        JWT_SECRET: str
        PINECONE_API_KEY: str
        PINECONE_INDEX: str

        SupabaseTables: List[str] = field(default_factory=lambda: [
            "account_plans",
            "research_data",
            "conversations",
            "messages",
            "users"
        ])

        EmbeddingModel: str = "models/text-embedding-004"

        PineconeDimensions: int = 768
        PineconeMetric: str = "cosine"
        PineconeCloud: str = "aws"
        PineconeRegion: str = "us-east-1"
        PineconeSearchK: int = 3
        PineconeThreshold: float = 0.7

        TavilySearchDepth: str = "advanced"
        PerplexityMaxResults: int = 5

        llmModel: str = "gemini-2.0-flash"
        llmTemperature: float = 0.0

        @classmethod
        def from_env(cls):
            """Load ENV credentials"""
            google_api_key = os.getenv("GOOGLE_API_KEY")
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
            database_url = os.getenv("DATABASE_URL")
            pinecone_api_key = os.getenv("PINECONE_API_KEY")
            pinecone_index = os.getenv("PINECONE_INDEX")
            jwt_secret = os.getenv("JWT_SECRET")

            missing = []
            if not google_api_key: missing.append("GOOGLE_API_KEY")
            if not pinecone_api_key: missing.append("PINECONE_API_KEY")
            if not pinecone_index: missing.append("PINECONE_INDEX_NAME")
            if not supabase_url: missing.append("SUPABASE_URL")
            if not supabase_key: missing.append("SUPABASE_KEY")
            if not tavily_api_key: missing.append("TAVILY_API_KEY")
            if not perplexity_api_key: missing.append("PERPLEXITY_API_KEY")
            if not database_url: missing.append("DATABASE_URL")
            if not jwt_secret: missing.append("JWT_SECRET")

            if missing:
                raise ValueError(f"Missing environment variables: {', '.join(missing)}")

            return cls(
                GOOGLE_API_KEY=google_api_key,
                SUPABASE_URL=supabase_url,
                SUPABASE_KEY=supabase_key,
                TAVILY_API_KEY=tavily_api_key,
                PERPLEXITY_API_KEY=perplexity_api_key,
                DATABASE_URL=database_url,
                JWT_SECRET=jwt_secret,
                PINECONE_API_KEY=pinecone_api_key,
                PINECONE_INDEX=pinecone_index
            )
