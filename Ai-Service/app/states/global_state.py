from typing import Any

class GlobalState:
    """
    Class to hold global state for services like Pinecone and Supabase clients.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalState, cls).__new__(cls)
            cls._instance.pinecone_client = None
            cls._instance.supabase_client = None
            cls._instance.pinecone_index = None 
        return cls._instance

    def set_pinecone(self, client: Any):
        self.pinecone_client = client

    def set_supabase(self, client: Any):
        self.supabase_client = client
        
    def get_pinecone(self):
        if not self.pinecone_client:
            raise RuntimeError("Pinecone client not initialized")
        return self.pinecone_client

    def get_supabase(self):
        if not self.supabase_client:
            raise RuntimeError("Supabase client not initialized")
        return self.supabase_client

services = GlobalState()
