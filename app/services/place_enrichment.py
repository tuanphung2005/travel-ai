"""
AI-based place enrichment service.
Estimates healing score and crowd level from textual and structural data.
Supports Vietnamese keywords.
"""

from typing import Dict, Any
import re

# --- Keywords for Inference (English + Vietnamese) ---

# Healing / Nature positive indicators
HEALING_KEYWORDS = {
    # English
    "nature", "park", "spa", "quiet", "healing", "garden", "beach", "lake", "forest", 
    "mountain", "relax", "peaceful", "tranquil", "retreat", "chill", "hill", "river",
    # Vietnamese
    "thiên nhiên", "công viên", "thư giãn", "yên tĩnh", "chữa lành", "vườn", "bãi biển",
    "hồ", "rừng", "núi", "yên bình", "thanh bình", "nghỉ dưỡng", "đồi", "sông", "suối",
    "mát mẻ", "thoáng đãng", "thanh tịnh", "chùa", "bình yên"
}

# Crowd / Busy positive indicators
CROWD_KEYWORDS = {
    # English
    "busy", "crowded", "nightlife", "market", "popular", "famous", "tourist", "street",
    "club", "bar", "party", "bustling", "lively", "mall", "shopping", "center", 
    "walking street", "walking", "pedestrian",
    # Vietnamese
    "nhộn nhịp", "đông đúc", "sôi động", "cuộc sống về đêm", "chợ", "nổi tiếng", 
    "phố đi bộ", "phố", "quán bar", "tiệc tùng", "náo nhiệt", "trung tâm", 
    "thương mại", "mua sắm", "sầm uất", "giới trẻ", "tấp nập"
}

# Hidden / Low crowd indicators
HIDDEN_KEYWORDS = {
    # English
    "hidden", "less crowded", "off the beaten path", "secret", "local", "secluded", "quiet",
    # Vietnamese
    "ẩn mình", "ít người", "vắng", "bí mật", "địa phương", "hoang sơ", "heo hút"
}


def _extract_text(doc: Dict[Any, Any]) -> str:
    """Extracts searchable text from a place document."""
    parts = []
    if "name" in doc and doc["name"]:
        parts.append(str(doc["name"]).lower())
    if "description" in doc and doc["description"]:
        parts.append(str(doc["description"]).lower())
    if "tags" in doc and hasattr(doc["tags"], '__iter__'):
        parts.extend([str(t).lower() for t in doc["tags"] if t])
    return " ".join(parts)


def estimate_healing_score(doc: Dict[Any, Any]) -> int:
    """
    Estimates a healing score (1-5) based on keywords, category, and review behavior.
    
    1 = extremely chaotic/stressful
    5 = deeply restorative/nature-focused
    """
    text = _extract_text(doc)
    category = str(doc.get("category", "")).upper()
    rating = float(doc.get("rating") or 0.0)
    
    score = 3.0  # Base score
    
    # 1. Category heuristics
    if category in {"PARK", "SPA", "WELLNESS"}:
        score += 1.5
    elif category == "NATURE":
        score += 2.0
    elif category in {"MARKET", "STREET_FOOD", "NIGHTLIFE"}:
        score -= 1.0
    
    # 2. Textual matching
    healing_matches = sum(1 for hw in HEALING_KEYWORDS if hw in text)
    crowd_matches = sum(1 for cw in CROWD_KEYWORDS if cw in text)
    
    # +0.5 for each healing term found, up to +1.5 max
    score += min(1.5, healing_matches * 0.5)
    
    # -0.5 for each busy/crowd term found, up to -1.5 max
    score -= min(1.5, crowd_matches * 0.5)
    
    # 3. Rating bump for highly rated places (if already leaning healing)
    if score >= 3.5 and rating >= 4.5:
        score += 0.5
        
    # Clamp between 1 and 5 and round
    final_score = int(round(max(1.0, min(5.0, score))))
    return final_score


def estimate_crowd_level(doc: Dict[Any, Any]) -> int:
    """
    Estimates a crowd level (1-5) based on category, keywords, and review count.
    
    1 = completely secluded
    5 = densely packed tourist hotspot
    """
    text = _extract_text(doc)
    category = str(doc.get("category", "")).upper()
    review_count = int(doc.get("reviewCount") or 0)
    
    score = 3.0  # Base score
    
    # 1. Category heuristics
    if category in {"MARKET", "STREET_FOOD", "MALL", "TRANSPORT"}:
        score += 1.0
    elif category in {"SPA", "WELLNESS", "NATURE", "PARK"}:
        score -= 0.5
        
    # 2. Review count as popularity proxy
    # Highly reviewed places are naturally more crowded
    if review_count > 5000:
        score += 1.5
    elif review_count > 1000:
        score += 1.0
    elif review_count > 500:
        score += 0.5
    elif review_count < 20: # extremely few reviews
        score -= 0.5
        
    # 3. Textual matching
    crowd_matches = sum(1 for cw in CROWD_KEYWORDS if cw in text)
    hidden_matches = sum(1 for hw in HIDDEN_KEYWORDS if hw in text)
    
    # +0.5 per busy word, max +1.5
    score += min(1.5, crowd_matches * 0.5)
    
    # -0.75 per hidden word, max -1.5
    score -= min(1.5, hidden_matches * 0.75)
    
    # Clamp between 1 and 5 and round
    final_score = int(round(max(1.0, min(5.0, score))))
    return final_score
