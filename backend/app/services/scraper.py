"""Website scraping service for extracting business information."""
import re
import json
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup

from app.db.database import get_db_connection


async def scrape_website(url: str, timeout: int = 30) -> dict:
    """
    Scrape a website and extract its content.
    
    Args:
        url: The URL to scrape
        timeout: Request timeout in seconds
        
    Returns:
        Dict with raw_content and parsed elements
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; KeystoneBot/1.0; +https://www.localkeystone.com)"
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            html_content = response.text
            soup = BeautifulSoup(html_content, "lxml")
            
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            title = soup.title.string if soup.title else ""
            
            meta_description = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag:
                meta_description = meta_tag.get("content", "")
            
            text_content = soup.get_text(separator="\n", strip=True)
            
            phone_pattern = r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}'
            phones = list(set(re.findall(phone_pattern, text_content)))
            
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = list(set(re.findall(email_pattern, text_content)))
            
            address_sections = []
            for tag in soup.find_all(["address", "div", "p"], class_=re.compile(r"address|location|contact", re.I)):
                address_sections.append(tag.get_text(strip=True))
            
            hours_sections = []
            for tag in soup.find_all(["div", "section", "table"], class_=re.compile(r"hours|schedule|time", re.I)):
                hours_sections.append(tag.get_text(separator=" | ", strip=True))
            
            services_sections = []
            for tag in soup.find_all(["div", "section", "ul"], class_=re.compile(r"service|menu|treatment|offering", re.I)):
                services_sections.append(tag.get_text(separator="\n", strip=True))
            
            pricing_sections = []
            for tag in soup.find_all(["div", "table", "ul"], class_=re.compile(r"price|pricing|cost|rate", re.I)):
                pricing_sections.append(tag.get_text(separator="\n", strip=True))
            
            return {
                "url": url,
                "title": title,
                "meta_description": meta_description,
                "raw_content": text_content[:50000],
                "parsed_data": {
                    "phones": phones[:5],
                    "emails": emails[:5],
                    "addresses": address_sections[:3],
                    "hours": hours_sections[:3],
                    "services": services_sections[:5],
                    "pricing": pricing_sections[:3]
                },
                "success": True
            }
            
    except httpx.RequestError as e:
        return {
            "url": url,
            "error": f"Request failed: {str(e)}",
            "success": False
        }
    except Exception as e:
        return {
            "url": url,
            "error": f"Scraping failed: {str(e)}",
            "success": False
        }


def parse_business_info(scraped_data: dict) -> dict:
    """
    Parse scraped data into structured business information.
    
    Args:
        scraped_data: The scraped website data
        
    Returns:
        Structured business info dict
    """
    parsed = scraped_data.get("parsed_data", {})
    
    info = {
        "phone": parsed.get("phones", [""])[0] if parsed.get("phones") else "",
        "email": parsed.get("emails", [""])[0] if parsed.get("emails") else "",
        "location": parsed.get("addresses", [""])[0] if parsed.get("addresses") else "",
        "hours_raw": parsed.get("hours", []),
        "services_raw": parsed.get("services", []),
        "pricing_raw": parsed.get("pricing", [])
    }
    
    return info


async def save_scraped_content(business_id: str, url: str, scraped_data: dict):
    """Save scraped content to database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        content_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO scraped_content (id, business_id, url, raw_content, parsed_data, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            content_id,
            business_id,
            url,
            scraped_data.get("raw_content", ""),
            json.dumps(scraped_data.get("parsed_data", {})),
            datetime.now().isoformat()
        ))
        conn.commit()
        
        return content_id
