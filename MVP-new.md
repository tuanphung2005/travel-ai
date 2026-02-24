# MVP Status Report

> Ký hiệu trạng thái:
> - ✅ **HOÀN THÀNH** — Đã triển khai đầy đủ
> - 🟡 **LÀM DỞ** — Có triển khai nhưng chưa đúng/đủ theo spec
> - ❌ **CHƯA LÀM** — Chưa triển khai

---

## 1) Mục tiêu (AI phải làm gì trong MVP)

Tạo lịch trình du lịch Hà Nội (1–4 ngày) được tối ưu theo:

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| Ràng buộc ngân sách (tổng + theo ngày) | ❌ **CHƯA LÀM** | Không có khái niệm budget trong toàn bộ code. Model `AIPlanRequest` và `ItineraryPlanner` không nhận `total_budget_vnd` hay `daily_budget_vnd`. |
| Sở thích mood (solo: 1 mood; group: phân bổ mood) | ❌ **CHƯA LÀM** | Hệ thống hiện dùng `travel_style` (sightseeing/relaxing/balanced) thay vì Mood model (RESET_HEALING, CHILL_CAFE, ...). |
| Chất lượng "healing" (đặc biệt với RESET & HEALING) | ❌ **CHƯA LÀM** | Không có `healing_score`, `crowd_level` trong Place model. |
| Tối thiểu hóa quãng đường di chuyển (thứ tự tuyến hợp lý) | ✅ **HOÀN THÀNH** | Sử dụng **Haversine distance**, **nearest-neighbor routing**, **geographic clustering** trong `planning_utils.py`. |
| Output nhanh | ✅ **HOÀN THÀNH** | Thuật toán deterministic, rule-based, không gọi LLM — chạy nhanh với ~120 địa điểm. |
| Tính quyết định tương đối (deterministic đủ dùng) | ✅ **HOÀN THÀNH** | Algorithm hoàn toàn deterministic, cùng input → cùng output. |
| Có thể chỉnh sửa thủ công mà không tự động regenerate lại | ✅ **HOÀN THÀNH** | Có endpoint `POST/DELETE .../stops/{place_id}` để thêm/xóa thủ công. Không auto-regenerate khi edit. |

---

## 2) Input / Output (AI Contract)

### 2.1 Input (bắt buộc tối thiểu)

#### Ngữ cảnh chuyến đi

| Field | Trạng thái | Ghi chú |
|---|---|---|
| `total_days: int (1–4)` | 🟡 **LÀM DỞ** | Tính từ `start_date`/`end_date`, không giới hạn 1–4 ngày. Không nhận trực tiếp `total_days`. |
| `total_budget_vnd: int` | ❌ **CHƯA LÀM** | Không có trong request model hay planner. |
| `daily_budget_vnd: int` | ❌ **CHƯA LÀM** | Không có. |
| `mode: "solo" \| "group"` | ❌ **CHƯA LÀM** | Không có khái niệm solo/group mode. |

#### Mood input

| Field | Trạng thái | Ghi chú |
|---|---|---|
| Solo: `mood: Mood` | ❌ **CHƯA LÀM** | Dùng `travel_style` thay vì Mood. |
| Group: `mood_distribution: {Mood: float}` | ❌ **CHƯA LÀM** | Không có. |

#### Dataset địa điểm (seed sẵn, 80–120 địa điểm)

| Field | Trạng thái | Ghi chú |
|---|---|---|
| `place_id, name, category` | 🟡 **LÀM DỞ** | Có `place_id`, `name`, `category` nhưng category là `ATTRACTION/HOTEL/RESTAURANT` — chưa mở rộng cho MVP moods (cafe, nature, ...). |
| `lat, lng` | ✅ **HOÀN THÀNH** | Lưu trong `location.coordinates` (GeoJSON). `PlaceData` có `latitude`, `longitude`. |
| `rating` | ✅ **HOÀN THÀNH** | Có trong Place model và `PlaceData`. |
| `estimated_cost_vnd` | ❌ **CHƯA LÀM** | Không có trong Place model. |
| `avg_visit_duration_min` | ❌ **CHƯA LÀM** | Duration được tính runtime từ `travel_style`, không lưu trên place. |
| `healing_score (1–5)` | ❌ **CHƯA LÀM** | Không có. |
| `crowd_level (1–5)` | ❌ **CHƯA LÀM** | Không có. |
| `image_url` (optional) | ❌ **CHƯA LÀM** | Không có trong model (nhưng optional cho AI). |

#### Runtime constraints (tùy chọn cho MVP)

| Field | Trạng thái | Ghi chú |
|---|---|---|
| `start_location` (mặc định: Hồ Gươm hoặc centroid chuyến đi) | ❌ **CHƯA LÀM** | Dùng place có rating cao nhất làm seed cho nearest-neighbor, không hỗ trợ start_location tùy chỉnh. |
| `max_places_per_day` (mặc định 5) | 🟡 **LÀM DỞ** | Max thay đổi theo `travel_style` (4–8), không có default 5 và không cho user tùy chỉnh. |
| `must_include_categories` / `exclude_categories` | ❌ **CHƯA LÀM** | Không có filter category. |

### 2.2 Output

#### Mỗi ngày (ItineraryPlan)

| Field | Trạng thái | Ghi chú |
|---|---|---|
| Danh sách place_ids đã được sắp xếp (1–5 địa điểm) | 🟡 **LÀM DỞ** | Trả về sorted places nhưng max stops phụ thuộc style (4–8), chưa cap 5 theo spec. |
| `total_estimated_cost_vnd` | ❌ **CHƯA LÀM** | Không tính cost. |
| `total_distance_km` (tính theo route) | 🟡 **LÀM DỞ** | Tính `distance_from_previous_km` cho từng stop, nhưng KHÔNG tổng hợp `total_distance_km` ở level day. |

#### Global metadata

| Field | Trạng thái | Ghi chú |
|---|---|---|
| `mood_used` / `mood_distribution_used` | ❌ **CHƯA LÀM** | Không có mood system. |
| `generated_at` | ❌ **CHƯA LÀM** | Không có timestamp trong response. |
| `candidate_pool_size` | ❌ **CHƯA LÀM** | Có mention trong `planning_notes` nhưng không phải field riêng. |
| `generation_time_ms` | ❌ **CHƯA LÀM** | Không đo thời gian. |
| `explanations` | 🟡 **LÀM DỞ** | Có `planning_notes` và `reason` per stop, nhưng không theo format spec ("được chọn vì healing_score >= 4"). |

#### Hard constraints

| Constraint | Trạng thái | Ghi chú |
|---|---|---|
| `total_estimated_cost_vnd(day) <= daily_budget_vnd` | ❌ **CHƯA LÀM** | Không có budget constraint. |
| `places_per_day <= 5` | ❌ **CHƯA LÀM** | Max stops phụ thuộc vào `travel_style` (4/6/8), không enforce cứng <= 5. |
| Thời gian generate <= 10 giây | ✅ **HOÀN THÀNH** | Thuật toán deterministic, rất nhanh. |

---

## 3) Mood Model (MVP)

### Danh sách Mood

| Mood | Trạng thái | Ghi chú |
|---|---|---|
| `RESET_HEALING` | ❌ **CHƯA LÀM** | Không tồn tại trong code. |
| `CHILL_CAFE` | ❌ **CHƯA LÀM** | Không tồn tại. |
| `NATURE_EXPLORE` | ❌ **CHƯA LÀM** | Không tồn tại. |
| `FOOD_LOCAL` | ❌ **CHƯA LÀM** | Không tồn tại. |

### 3.1 Mood scoring (cấp độ địa điểm)

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| Định nghĩa `moodScore(place, mood)` (0..1 hoặc 0..100) | ❌ **CHƯA LÀM** | Hệ thống dùng `calculate_place_score(place, style)` dựa trên rating/review/category — không có mood score. |
| Bonus theo category (vd: cafe cho CHILL_CAFE) | ❌ **CHƯA LÀM** | Category bonus hiện gắn với `travel_style`, không với mood. |
| Bonus `healing_score` cho RESET_HEALING | ❌ **CHƯA LÀM** | `healing_score` chưa tồn tại. |
| Penalty `crowd_level` cho RESET_HEALING | ❌ **CHƯA LÀM** | `crowd_level` chưa tồn tại. |
| Bonus nhẹ theo rating | ✅ **HOÀN THÀNH** | `calculate_place_score` có weight 40% cho rating. |

### 3.2 Phân bổ mood cho group

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| `finalScore(place) = Σ mood_distribution[m] * moodScore(place, m)` | ❌ **CHƯA LÀM** | Không có group mood distribution. |

---

## 4) Chiến lược tối ưu (MVP Algorithm)

### 4.1 Bước A — Lọc candidate

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| Loại `estimated_cost_vnd > daily_budget_vnd` | ❌ **CHƯA LÀM** | Không có cost data hay budget filtering. |
| Áp dụng filter theo mood | ❌ **CHƯA LÀM** | Không có mood filter. |
| Rank candidate theo `finalScore` và giữ top K (30–50) | 🟡 **LÀM DỞ** | Có rank theo `calculate_place_score` nhưng dùng clustering thay vì top-K selection. Candidate pool không giới hạn K. |

### 4.2 Bước B — Chọn địa điểm theo ngân sách (Day packing)

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| Greedy theo `(finalScore / cost)` | ❌ **CHƯA LÀM** | Dùng clustering + time-based packing, không greedy theo score/cost ratio. |
| Check ngân sách còn lại | ❌ **CHƯA LÀM** | Không có budget checking. |
| Dừng khi đủ 5 hoặc không còn phù hợp | 🟡 **LÀM DỞ** | Dừng khi max stops (theo style) hoặc hết available time, nhưng không dừng theo budget. |
| Đảm bảo đa dạng category (không >2 cùng loại/ngày) | ❌ **CHƯA LÀM** | Không có category diversity constraint. |

### 4.3 Bước C — Sắp xếp route (giảm khoảng cách)

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| Tính khoảng cách pairwise bằng Haversine | ✅ **HOÀN THÀNH** | `haversine_distance()` + `build_distance_matrix()` trong `planning_utils.py`. |
| Nearest-neighbor từ `start_location` | 🟡 **LÀM DỞ** | Dùng nearest-neighbor nhưng start từ place có rating cao nhất, không từ `start_location` tùy chỉnh. |
| Optional: 2-opt improvement | ❌ **CHƯA LÀM** | Chỉ có nearest-neighbor, chưa có 2-opt. |

### 4.4 Bước D — Phân bổ nhiều ngày

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| Không lặp lại địa điểm giữa các ngày | ✅ **HOÀN THÀNH** | Clustering phân bổ mỗi place vào đúng 1 cluster/day. |
| Dùng `used_place_ids` global set | 🟡 **LÀM DỞ** | Dùng clustering để phân chia, không dùng explicit `used_place_ids` set — nhưng kết quả tương đương (không duplicate). |
| Lặp qua từng ngày và chọn từ candidate còn lại | 🟡 **LÀM DỞ** | Dùng clustering thay vì greedy day-by-day selection từ candidate pool. |

---

## 5) Special Rules (theo product doc)

### 5.1 Reset & Healing rules

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| Weight mạnh `healing_score` | ❌ **CHƯA LÀM** | Không có healing_score. |
| Penalize `crowd_level` | ❌ **CHƯA LÀM** | Không có crowd_level. |
| Nếu không đủ: cho phép `healing_score = 3` | ❌ **CHƯA LÀM** | Không có fallback logic. |
| Messaging: "Ngân sách/nguồn địa điểm hạn chế..." | ❌ **CHƯA LÀM** | Không có special messaging. |

### 5.2 Hỗ trợ messaging về ngân sách

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| `spent_today` | ❌ **CHƯA LÀM** | Không track chi phí. |
| `remaining_today` | ❌ **CHƯA LÀM** | Không track chi phí. |
| `saved_vs_budget` | ❌ **CHƯA LÀM** | Không track chi phí. |

---

## 6) Regeneration & Edit Behavior (Quan trọng cho collaboration)

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| AI chỉ generate khi user bấm "Generate itinerary" / "Re-generate" | ✅ **HOÀN THÀNH** | Phải gọi `POST /{journey_id}/ai-plan` rõ ràng. |
| Owner only regenerate với group mode | ❌ **CHƯA LÀM** | Không có authorization check cho owner. |
| Sau khi chỉnh sửa thủ công: Không auto-regenerate | ✅ **HOÀN THÀNH** | Manual edit endpoints (`add_stop_to_day`, `remove_stop_from_day`) không trigger regenerate. |
| "Improve route order only" (nice-to-have) | ❌ **CHƯA LÀM** | Có `reorder_stops` trong repository nhưng không expose endpoint nào cho "improve route order only". |

---

## 7) Quality Bar / Acceptance Tests (AI MVP)

### 7.1 Ràng buộc deterministic

| Ràng buộc | Trạng thái | Ghi chú |
|---|---|---|
| `max(len(day.places)) <= 5` | ❌ **CHƯA LÀM** | Max stops phụ thuộc `travel_style`: sightseeing=8, balanced=6, relaxing=4. Không enforce cứng <= 5. |
| `day.total_cost <= daily_budget` | ❌ **CHƯA LÀM** | Không có budget/cost system. |
| Tất cả `place_ids` tồn tại | ✅ **HOÀN THÀNH** | Places luôn fetched từ MongoDB trước khi planning. |
| Không duplicate giữa các ngày | ✅ **HOÀN THÀNH** | Clustering đảm bảo mỗi place chỉ xuất hiện 1 lần. |

### 7.2 Performance

| Ràng buộc | Trạng thái | Ghi chú |
|---|---|---|
| 120 địa điểm, generate <= 10 giây | ✅ **HOÀN THÀNH** | Algorithm O(n²) cho distance matrix + O(n) clustering — rất nhanh. |

### 7.3 Mood correctness (sanity check)

| Ràng buộc | Trạng thái | Ghi chú |
|---|---|---|
| RESET_HEALING: >= 60% places có `healing_score >= 4` | ❌ **CHƯA LÀM** | Không có mood system và healing_score. |
| CHILL_CAFE: >= 1 cafe/ngày | ❌ **CHƯA LÀM** | Không có mood system. |

---

## 8) Observability (Logging cho MVP)

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| `tripId`, `userId` | ❌ **CHƯA LÀM** | Không có structured logging. |
| `mood` / `mood_distribution` | ❌ **CHƯA LÀM** | Mood system chưa có. |
| `budgets` | ❌ **CHƯA LÀM** | Budget system chưa có. |
| `candidate_pool_size` | 🟡 **LÀM DỞ** | Có ghi vào `planning_notes` (text) nhưng không phải structured log field. |
| Danh sách địa điểm được chọn và score | ❌ **CHƯA LÀM** | Scores tính nội bộ nhưng không được log/trả về. |
| `time_ms` | ❌ **CHƯA LÀM** | Không đo/log thời gian generate. |
| `reason_codes` khi fallback | ❌ **CHƯA LÀM** | Không có fallback reason codes. |

---

## Tổng kết

### ✅ Đã hoàn thành tốt (9 items)
- Haversine distance calculation
- Nearest-neighbor route optimization
- Geographic clustering cho multi-day
- Deterministic algorithm (cùng input → cùng output)
- Output nhanh (< 10s)
- Chỉnh sửa thủ công không auto-regenerate
- AI chỉ generate khi user bấm
- Tất cả place_ids tồn tại (từ DB)
- Không duplicate place giữa các ngày

### 🟡 Làm dở (8 items)
- `total_days` tính từ dates nhưng không giới hạn 1–4
- `max_places_per_day` phụ thuộc style, không default 5
- `total_distance_km` tính per-stop nhưng chưa tổng hợp per-day
- Candidate ranking có nhưng dùng clustering thay vì top-K
- Nearest-neighbor start từ highest rating, không từ `start_location`
- Multi-day allocation dùng clustering thay vì greedy + used_set
- `candidate_pool_size` ghi planning_notes nhưng không structured
- `explanations` có `planning_notes`/`reason` nhưng chưa đúng spec format

### ❌ Chưa làm (phần lớn MVP core) (30+ items)
- **Budget system** (total_budget_vnd, daily_budget_vnd, cost checking, budget messaging)
- **Mood system** hoàn toàn (4 moods, moodScore, mood_distribution, solo/group mode)
- **Place data fields** (estimated_cost_vnd, avg_visit_duration_min, healing_score, crowd_level)
- **Candidate filtering** theo mood + budget
- **Greedy day packing** theo (finalScore / cost)
- **Category diversity** constraint (không >2 cùng loại/ngày)
- **2-opt** route improvement
- **Reset & Healing** special rules + fallback messaging
- **Response metadata** (generated_at, generation_time_ms, mood_used, candidate_pool_size)
- **Observability / Structured logging**
- **Owner-only regeneration** cho group mode
- **"Improve route order only"** endpoint
- **Acceptance tests** cho budget + mood correctness
