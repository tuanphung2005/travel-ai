import re
import unicodedata
import difflib

def canonical_name(name: str) -> str:
    # 1. Normalize unicode
    normalized = unicodedata.normalize('NFKD', str(name or "")).encode('ASCII', 'ignore').decode('utf-8').lower()
    
    # 2. Remove parenthesized text
    normalized = re.sub(r"\([^)]*\)", " ", normalized)
    
    # 3. Strip known branch indicators
    normalized = re.sub(r"(@|-|\|).*$", " ", normalized)
    
    # 4. Remove apostrophes so "4p's" and "4p’s" become "4ps"
    normalized = re.sub(r"[']", "", normalized)
    
    # 5. Remove any non-alphanumeric chars
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    
    # 6. Remove common Vietnamese branch keywords
    normalized = re.sub(r"\b(branch|chi nhanh|co so|coso|cn|cs)\s*\d*\w*\b", " ", normalized)
    
    # 7. Remove "met \d+" at the end ONLY
    normalized = re.sub(r"\bmet\s+\d+\s*$", " ", normalized)
    
    # 8. Final cleanup: remove isolated trailing numbers
    normalized = re.sub(r"\b\d+\s*$", " ", normalized)
    
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized

names = [
    "MẸT Vietnamese restaurant & Vegetarian Food 1",
    "MẸT Vietnamese restaurant & Vegetarian Food 3",
    "MẸT Vietnamese Restaurant & Vegetarian Met 2",
    "MẸT Vietnamese restaurant & Vegetarian Food 5",
    "MẸT Vietnamese restaurant & Vegetarian Met 4",
    "Pizza 4P’s Tràng Tiền",
    "Pizza 4P's @Phan Kế Bính",
    "Long Wang - Lẩu Hấp Thủy Nhiệt Hồng Kông - 409 Minh Khai",
    "Gánh Hà Nội",
    "Long Wang - Lẩu Hấp Thủy Nhiệt Hồng Kông 123",
]

canonical_names = [canonical_name(n) for n in names]

# Let's test grouping with difflib
groups = []
for orig, can in zip(names, canonical_names):
    matched_group = None
    for group in groups:
        # Check if canonical name is very similar to an existing group's canonical name
        similarity = difflib.SequenceMatcher(None, can, group['canonical']).ratio()
        if similarity > 0.85 or can.startswith(group['canonical']) or group['canonical'].startswith(can):
            matched_group = group
            break
            
    if matched_group:
        matched_group['items'].append(orig)
    else:
        groups.append({'canonical': can, 'items': [orig]})

with open("out.txt", "w", encoding="utf-8") as f:
    for g in groups:
        f.write(f"Group: {g['canonical']}\n")
        for item in g['items']:
            f.write(f"  - {item}\n")
