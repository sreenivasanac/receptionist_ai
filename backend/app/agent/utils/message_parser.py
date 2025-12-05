"""Message parser utility for extracting structured data from chat messages."""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedMessage:
    """Parsed message with extracted metadata."""
    text: str
    slot_id: Optional[str] = None
    service_id: Optional[str] = None


class MessageParser:
    """Parser for extracting structured data from chat messages."""
    
    SLOT_PATTERN = re.compile(r'\[slot:([^\]]+)\]')
    SERVICE_ID_PATTERN = re.compile(r'\[service_id:([^\]]+)\]')
    
    @classmethod
    def parse(cls, message: str) -> ParsedMessage:
        """
        Parse a message and extract any embedded metadata.
        
        Args:
            message: The raw message string
            
        Returns:
            ParsedMessage with cleaned text and extracted metadata
        """
        text = message
        slot_id = None
        service_id = None
        
        # Extract slot_id if present
        slot_match = cls.SLOT_PATTERN.search(text)
        if slot_match:
            slot_id = slot_match.group(1)
            text = cls.SLOT_PATTERN.sub('', text).strip()
        
        # Extract service_id if present
        service_match = cls.SERVICE_ID_PATTERN.search(text)
        if service_match:
            service_id = service_match.group(1)
            text = cls.SERVICE_ID_PATTERN.sub('', text).strip()
        
        return ParsedMessage(
            text=text,
            slot_id=slot_id,
            service_id=service_id
        )
    
    @classmethod
    def extract_slot_id(cls, message: str) -> tuple[str, Optional[str]]:
        """Extract slot_id from message. Returns (clean_message, slot_id)."""
        match = cls.SLOT_PATTERN.search(message)
        if match:
            slot_id = match.group(1)
            clean_message = cls.SLOT_PATTERN.sub('', message).strip()
            return clean_message, slot_id
        return message, None
    
    @classmethod
    def extract_service_id(cls, message: str) -> tuple[str, Optional[str]]:
        """Extract service_id from message. Returns (clean_message, service_id)."""
        match = cls.SERVICE_ID_PATTERN.search(message)
        if match:
            service_id = match.group(1)
            clean_message = cls.SERVICE_ID_PATTERN.sub('', message).strip()
            return clean_message, service_id
        return message, None
