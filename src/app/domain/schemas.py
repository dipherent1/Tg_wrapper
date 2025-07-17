from pydantic import BaseModel
from typing import List, Optional

# --- Tag Schemas ---
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass # No extra fields needed for creation

class Tag(TagBase):
    id: int
    
    class Config:
        from_attributes = True # Pydantic V2
        # orm_mode = True for Pydantic V1

# --- Channel Schemas ---
class ChannelBase(BaseModel):
    telegram_channel_id: int
    name: str
    type: Optional[str] = None

class ChannelCreate(ChannelBase):
    pass

class Channel(ChannelBase):
    id: int
    tags: List[Tag] = [] # When we read a channel, we want to see its tags

    class Config:
        from_attributes = True # Pydantic V2
        # orm_mode = True for Pydantic V1

# Update Tag schema to prevent circular dependency issues
# Now that 'Channel' is defined, we can add it here.
class Tag(Tag): # Re-opening the class to add the new field
    channels: List[Channel] = []

# NEW: Add User schemas
class UserBase(BaseModel):
    telegram_user_id: int
    first_name: str
    username: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    
    class Config:
        from_attributes = True