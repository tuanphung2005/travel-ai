import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.planning_utils import deduplicate_similar_places
from app.planning_types import PlaceData

names = [
    "MẸT Vietnamese restaurant & Vegetarian Food 1",
    "MẸT Vietnamese restaurant & Vegetarian Food 3",
    "MẸT Vietnamese Restaurant & Vegetarian Met 2",
    "Pizza 4P’s Tràng Tiền",
    "MẸT Vietnamese restaurant & Vegetarian Food 5",
    "MẸT Vietnamese restaurant & Vegetarian Met 4",
    "Pizza 4P's @Phan Kế Bính",
    "Long Wang - Lẩu Hấp Thủy Nhiệt Hồng Kông - 409 Minh Khai",
    "Gánh Hà Nội",
    "Katze Vegan & Vegetarian",
    "Cái Mâm Restaurant",
    "Hanoi Food Culture",
    "Timeline Coffee & Restaurant",
    "Nhà Hàng Ban Công",
    "Phở Gà Huyền Hương"
]

places = []
for i, name in enumerate(names):
    places.append(PlaceData(
        id=f"id_{i}",
        name=name,
        latitude=0.0,
        longitude=0.0,
        category="RESTAURANT",
        rating=4.9,
        review_count=100 + i,
        tags=[],
        estimated_cost_vnd=150000,
        avg_visit_duration_min=60,
        healing_score=0,
        crowd_level=0,
        price_level=0
    ))

deduped = deduplicate_similar_places(places)

print(f"Original: {len(places)} places")
print(f"Deduped: {len(deduped)} places")
for p in deduped:
    print(f" - {p.name}")
