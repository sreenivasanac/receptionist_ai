"""LLM-based extraction service using OpenAI structured outputs."""
from openai import OpenAI

from app.config import settings
from app.models.extracted_config import ExtractedBusinessConfig


EXTRACTION_PROMPT = """You are an expert at extracting business information from website content.

Extract the following information if present:
- Business name
- Full address/location
- Phone number (format: (XXX) XXX-XXXX if US)
- Email address
- Business hours for each day of the week (use 24-hour format HH:MM)
- Services offered with descriptions, duration, and prices
- Business policies (cancellation, walk-ins, deposits)
- FAQs (questions and answers found on the site)

Rules:
- Only extract information that is explicitly stated in the content
- Use null for fields that cannot be found
- For hours, use day names in lowercase (monday, tuesday, etc.)
- For prices, extract as numbers without currency symbols
- For durations, convert to minutes (e.g., "1 hour" = 60)
- Extract all FAQs you can find, even if they're not in a dedicated FAQ section
- Look for Q&A patterns, policy explanations, and common questions answered in the content"""


def extract_with_llm(raw_content: str) -> ExtractedBusinessConfig:
    """
    Use OpenAI structured outputs to extract business information.
    
    Args:
        raw_content: Combined raw text content from scraped website pages
        
    Returns:
        ExtractedBusinessConfig with parsed business information
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Limit content to avoid token limits (~15k chars ≈ 4k tokens)
    truncated_content = raw_content[:15000]
    
    completion = client.beta.chat.completions.parse(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": f"Extract business information from this website content:\n\n{truncated_content}"}
        ],
        response_format=ExtractedBusinessConfig
    )
    
    return completion.choices[0].message.parsed


def extract_with_llm_safe(raw_content: str) -> tuple[ExtractedBusinessConfig | None, str | None]:
    """
    Safely extract business info, returning error message on failure.
    
    Returns:
        Tuple of (extracted_config, error_message)
    """
    try:
        result = extract_with_llm(raw_content)
        return result, None
    except Exception as e:
        return None, str(e)
