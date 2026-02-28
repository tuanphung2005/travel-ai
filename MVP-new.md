# MVP Status Report (Updated 2026-02-28)

> Ký hiệu trạng thái:
> - ✅ **HOÀN THÀNH** — Đã triển khai đầy đủ
> - 🟡 **LÀM DỞ** — Có triển khai nhưng chưa đủ acceptance/coverage
> - ❌ **CHƯA LÀM** — Chưa triển khai

---

## 1) Mục tiêu MVP

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| Ràng buộc ngân sách (tổng + theo ngày) | ✅ | `total_budget_vnd`, `daily_budget_vnd`, cap theo ngày + không vượt tổng ngân sách nếu có. |
| Mood solo/group | ✅ | `mode=solo/group`, `mood`, `mood_distribution`, scoring có weighted blend. |
| Healing quality (RESET_HEALING) | ✅ | Có `healing_score`, `crowd_level`, fallback từ >=4 xuống >=3 + reason code. |
| Tối thiểu hóa quãng đường | ✅ | Haversine + nearest-neighbor + 2-opt (optional trong optimizer). |
| Output nhanh, deterministic | ✅ | Rule-based, không random, không LLM inference. |
| Manual edit không auto-regenerate | ✅ | Add/remove stop không trigger generate lại. |

---

## 2) Input/Output Contract

### 2.1 Input

| Field | Trạng thái | Ghi chú |
|---|---|---|
| `total_days (1–4)` | ✅ | Validate từ journey range; reject ngoài [1..4]. |
| `total_budget_vnd`, `daily_budget_vnd` | ✅ | Có trong request + planner. |
| `mode: solo/group` | ✅ | Có validator theo mode. |
| `mood` (solo) | ✅ | Bắt buộc với `solo`. |
| `mood_distribution` (group) | ✅ | Bắt buộc với `group` và tổng trọng số > 0. |
| `start_location` | ✅ | Hỗ trợ tùy chọn; mặc định centroid nếu không truyền. |
| `max_places_per_day` | ✅ | Hard cap <= 5. |
| `must_include_categories` / `exclude_categories` | ✅ | Có áp dụng trong planning flow. |

### 2.2 Output

| Field | Trạng thái | Ghi chú |
|---|---|---|
| Mỗi ngày: list places đã sắp xếp | ✅ | Có route order tối ưu, tối đa 5 stop/ngày. |
| `total_estimated_cost_vnd` / `total_distance_km` | ✅ | Có ở từng day plan. |
| `spent_today` / `remaining_today` / `saved_vs_budget` | ✅ | Có đầy đủ theo ngày. |
| `mood_used` / `mood_distribution_used` | ✅ | Có trong response metadata. |
| `generated_at` / `candidate_pool_size` / `generation_time_ms` | ✅ | Có trong response metadata. |
| `explanations` | ✅ | Có giải thích per-day + reason per-stop. |

---

## 3) Mood Model

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| 4 mood (`RESET_HEALING`, `CHILL_CAFE`, `NATURE_EXPLORE`, `FOOD_LOCAL`) | ✅ | Đã khai báo trong model + scoring map. |
| `moodScore(place, mood)` | ✅ | 0..100, gồm rating + category bonus + rule riêng RESET. |
| Group blend: Σ distribution * moodScore | ✅ | Đã triển khai `blended_mood_score`. |
| RESET fallback + messaging | ✅ | Có fallback threshold + `reason_codes` + planning notes. |
| CHILL_CAFE >=1 cafe/ngày nếu khả thi | ✅ | Có cố gắng ép chọn cafe trước greedy pass. |

---

## 4) Strategy / Algorithm

| Bước | Trạng thái | Ghi chú |
|---|---|---|
| A. Candidate filtering/ranking | ✅ | Filter budget/category/mood + top-K (30..50). |
| B. Day packing | ✅ | Greedy theo `(finalScore / cost)`, check budget/time, cap 5. |
| C. Route optimization | ✅ | Haversine pairwise, start_location support, 2-opt refine. |
| D. Multi-day allocation | ✅ | `used_place_ids` global set, không duplicate giữa ngày. |

---

## 5) Regeneration & Collaboration

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| AI chỉ chạy khi gọi endpoint generate | ✅ | `POST /api/v1/journeys/{journey_id}/ai-plan`. |
| Group mode: owner-only regenerate | ✅ | Cần `requester_user_id`; kiểm tra owner, trả 403 nếu không phải owner. |
| Manual chỉnh sửa không auto-regenerate | ✅ | Endpoints add/remove giữ nguyên behavior. |
| Improve route order only | ✅ | `POST /api/v1/journeys/{journey_id}/days/{day_number}/improve-route-order`. |

---

## 6) Observability

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| `tripId`, `userId`, mood, budgets | ✅ | Structured event `AI_PLANNING_EVENT`. |
| `candidate_pool_size`, selected places + score | ✅ | Có trong log payload. |
| `time_ms` | ✅ | Có `generation_time_ms` + log field. |
| `reason_codes` fallback | ✅ | Có reason code list khi fallback/constraint miss. |

---

## 7) Quality Bar / Acceptance

| Ràng buộc | Trạng thái | Ghi chú |
|---|---|---|
| `max(len(day.places)) <= 5` | ✅ | Enforced bằng request + planner cap. |
| `day.total_cost <= daily_budget` | ✅ | Enforced trong day packing. |
| Không duplicate giữa ngày | ✅ | Enforced bằng global used set. |
| Generate nhanh (<=10s với ~120 places) | 🟡 | Kiến trúc đã tối ưu, nhưng chưa có benchmark test script tự động trong repo. |
| Sanity test tự động cho mood rules | 🟡 | Rule đã có trong code, chưa có test automation riêng cho metrics 60%/>=1 cafe. |

---

## 8) Remaining Work (practical next)

1. Thêm test automation cho acceptance checks (budget cap, no-duplicate, mood sanity).
2. Thêm benchmark script để xác nhận SLA 10 giây với dataset lớn.
3. Chuẩn hóa category taxonomy ở dataset nguồn để giảm phụ thuộc heuristic từ tags.
