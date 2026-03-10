import re
import unicodedata

def canonical_name(name: str) -> str:
    # 1. Strip accents
    normalized = unicodedata.normalize('NFKD', str(name or "")).encode('ASCII', 'ignore').decode('utf-8').lower()
    
    # 2. Remove parenthesized text
    normalized = re.sub(r"\([^)]*\)", " ", normalized)
    
    # 3. Remove branch indicators like "@Location", "- Location", "cs 1", "branch 1"
    normalized = re.sub(r"(@|-).*$", " ", normalized)
    normalized = re.sub(r"\b(branch|chi nhanh|co so|cn|cs)\s*\d*\w*\b", " ", normalized)
    
    # Replace non-alphanumeric with space
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    
    # 4. Remove trailing numbers or isolated trailing words that look like branch numbers (like "1", "2")
    # Also remove "met 2" at the end if it's there?
    # Simple trailing digits
    normalized = re.sub(r"\b\d+\s*$", " ", normalized)
    
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized

names = [
    "MẸT Vietnamese restaurant & Vegetarian Food 1",
    "MẸT Vietnamese restaurant & Vegetarian Food 3",
    "MẸT Vietnamese Restaurant & Vegetarian Met 2",
    "Pizza 4P’s Tràng Tiền",
    "MẸT Vietnamese restaurant & Vegetarian Food 5",
    "MẸT Vietnamese restaurant & Vegetarian Met 4",
    "Pizza 4P's @Phan Kế Bính",
    "Long Wang - Lẩu Hấp Thủy Nhiệt Hồng Kông - 409 Minh Khai",
    "Katze Vegan & Vegetarian",
    "Cái Mâm Restaurant",
    "Hanoi Food Culture",
    "Timeline Coffee & Restaurant",
    "Nhà Hàng Ban Công",
    "Phở Gà Huyền Hương"
]

with open("out.txt", "w") as f:
    for n in names:
        f.write(f"{n!r:60} -> {canonical_name(n)!r}\n")
