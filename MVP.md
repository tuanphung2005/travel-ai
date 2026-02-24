1) Mục tiêu (AI phải làm gì trong MVP) 

Tạo lịch trình du lịch Hà Nội (1–4 ngày) được tối ưu theo: 

    Ràng buộc ngân sách (tổng + theo ngày) 

    Sở thích mood (solo: 1 mood; group: phân bổ mood) 

    Chất lượng “healing” (đặc biệt với RESET & HEALING) 

    Tối thiểu hóa quãng đường di chuyển (thứ tự tuyến hợp lý) 

Output phải: 

    Nhanh 

    Tính quyết định tương đối (deterministic đủ dùng) 

    Có thể chỉnh sửa thủ công mà không tự động regenerate lại 

 

2) Input / Output (AI Contract) 

2.1 Input (bắt buộc tối thiểu) 

Ngữ cảnh chuyến đi 

    total_days: int (1–4) 

    total_budget_vnd: int 

    daily_budget_vnd: int (= total_budget / total_days) 

    mode: "solo" | "group" 

Mood input 

    Solo: 

    mood: Mood 

    Group: 

    mood_distribution: {Mood: float} (tổng = 1.0) 

 

Dataset địa điểm (seed sẵn, 80–120 địa điểm) 

Mỗi địa điểm phải có: 

    place_id, name, category 

    lat, lng 

    rating 

    estimated_cost_vnd 

    avg_visit_duration_min 

    healing_score (1–5) 

    crowd_level (1–5) 

    image_url (optional cho AI) 

 

Runtime constraints (tùy chọn cho MVP) 

    start_location (mặc định: Hồ Gươm hoặc centroid chuyến đi) 

    max_places_per_day (mặc định 5) 

    must_include_categories hoặc exclude_categories (optional) 

 

2.2 Output 

AI trả về một ItineraryPlan: 

Với mỗi ngày d trong 1..total_days: 

    Danh sách place_ids đã được sắp xếp (1–5 địa điểm) 

    total_estimated_cost_vnd 

    total_distance_km (tính theo route) 

 

Global metadata 

    mood_used hoặc mood_distribution_used 

    generated_at 

    candidate_pool_size 

    generation_time_ms 

    (optional) explanations — ví dụ: “được chọn vì healing_score >= 4” 

 

Hard constraints 

    total_estimated_cost_vnd(day) <= daily_budget_vnd 

    places_per_day <= 5 

    Thời gian generate <= 10 giây 

 

3) Mood Model (MVP) 

Danh sách Mood 

    RESET_HEALING 

    CHILL_CAFE 

    NATURE_EXPLORE 

    FOOD_LOCAL 

 

3.1 Mood scoring (cấp độ địa điểm) 

Định nghĩa moodScore(place, mood) (0..1 hoặc 0..100). 

MVP có thể rule-based: 

Ví dụ tín hiệu: 

    Bonus theo category (vd: cafe cho CHILL_CAFE) 

    Bonus healing_score cho RESET_HEALING 

    Penalty crowd_level cho RESET_HEALING 

    Bonus nhẹ theo rating 

 

3.2 Phân bổ mood cho group 

Với group mode: 

finalScore(place) = Σ mood_distribution[m] * moodScore(place, m) 
 

Cách này giúp tránh cần LLM trong MVP nhưng vẫn tạo cảm giác “AI cá nhân hóa”. 

 

4) Chiến lược tối ưu (MVP Algorithm) 

Mục tiêu: triển khai được, dễ giải thích, nhanh với ~120 địa điểm. 

 

4.1 Bước A — Lọc candidate 

Theo từng trip/ngày: 

    Loại địa điểm có estimated_cost_vnd > daily_budget_vnd (không thể fit). 

    Áp dụng filter theo mood: 

Ví dụ với RESET_HEALING: 

    Ưu tiên healing_score >= 4 

    crowd_level <= 3 

(MVP: xử lý như soft constraint nếu pool quá nhỏ) 

    Rank candidate theo finalScore và giữ top K (vd: K=30–50). 

 

4.2 Bước B — Chọn địa điểm theo ngân sách (Day packing) 

Mục tiêu: chọn tối đa 5 địa điểm/ngày mà không vượt ngân sách. 

Cách MVP (đủ tốt): 

    Greedy theo (finalScore / cost) 

    Check ngân sách còn lại 

    Dừng khi: 

    Đủ 5 địa điểm 

    Hoặc không còn địa điểm phù hợp ngân sách 

Optional: 

    Đảm bảo đa dạng category (không >2 cùng loại/ngày) 

 

4.3 Bước C — Sắp xếp route (giảm khoảng cách) 

Sau khi chọn địa điểm cho ngày đó: 

    Tính khoảng cách pairwise bằng Haversine 

    Dùng: 

    Nearest-neighbor từ start_location 

    Optional: cải thiện bằng 2-opt (nhanh với <=5 nodes) 

 

4.4 Bước D — Phân bổ nhiều ngày 

    Không lặp lại địa điểm giữa các ngày 

    Dùng used_place_ids global set 

    Lặp qua từng ngày và chọn từ candidate còn lại 

 

5) Special Rules (theo product doc) 

5.1 Reset & Healing rules 

    Weight mạnh healing_score 

    Penalize crowd_level 

Nếu không đủ địa điểm phù hợp: 

    Cho phép healing_score = 3 

    Thêm messaging: 

“Ngân sách/nguồn địa điểm hạn chế nên có vài điểm đông hơn một chút.” 

 

5.2 Hỗ trợ messaging về ngân sách 

AI nên trả thêm: 

    spent_today 

    remaining_today 

    saved_vs_budget 

 

6) Regeneration & Edit Behavior (Quan trọng cho collaboration) 

    AI chỉ generate khi user bấm: 

    “Generate itinerary” 

    “Re-generate” (owner only với group mode) 

    Sau khi chỉnh sửa thủ công: 

    Không auto-regenerate 

    Optional: 

    “Improve route order only” (nice-to-have) 

 

7) Quality Bar / Acceptance Tests (AI MVP) 

7.1 Ràng buộc deterministic 

Với mọi plan: 

    max(len(day.places)) <= 5 

    day.total_cost <= daily_budget 

    Tất cả place_ids tồn tại 

    Không duplicate giữa các ngày (trừ khi cho phép) 

 

7.2 Performance 

    Với 120 địa điểm, generate <= 10 giây trên server thông thường. 

 

7.3 Mood correctness (sanity check) 

    Với RESET_HEALING: 

    Ít nhất 60% địa điểm có healing_score >= 4 nếu dataset cho phép. 

    Với CHILL_CAFE: 

    Ít nhất 1 cafe/ngày nếu dataset cho phép. 

(Đây là soft acceptance check phụ thuộc seed data.) 

 

8) Observability (Logging cho MVP) 

Log mỗi lần generate: 

    tripId, userId (hoặc anonymized) 

    mood / mood_distribution 

    budgets 

    candidate_pool_size 

    Danh sách địa điểm được chọn và score của chúng 

    time_ms 

    reason_codes khi fallback (vd: “not enough healing>=4”) 

 