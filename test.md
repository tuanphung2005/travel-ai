1. MVP AI Planning - High Level Flow
The big picture. Three layers:

INPUT — Everything the user/system provides: total_days (1–4), total_budget_vnd, daily_budget_vnd, mode (solo/group), mood or mood_distribution, the place dataset (80–120 places with fields like healing_score, crowd_level, estimated_cost_vnd), and optional runtime constraints (start_location, max_places_per_day, category filters).
ALGORITHM — The 4-step pipeline: Filter Candidates → Day Packing → Route Optimization → Multi-Day Allocation. Each step feeds into the next sequentially.
OUTPUT — What the API returns: per-day sorted places with cost and distance, global metadata (mood_used, generated_at, generation_time_ms, candidate_pool_size, explanations), and hard constraints that must always hold (cost ≤ budget, places ≤ 5, time ≤ 10s).
2. Step A - Candidate Filtering
How the 80–120 raw places get narrowed down to a usable candidate pool:

Cost filter — Any place where estimated_cost_vnd > daily_budget_vnd is immediately removed (can't possibly fit in a single day).
Mode branch — Solo mode calculates moodScore(place, mood) for one mood. Group mode calculates finalScore = Σ mood_distribution[m] × moodScore(place, m) across all moods.
Mood-specific soft filters — For RESET_HEALING specifically: prefer healing_score ≥ 4 and crowd_level ≤ 3. If the pool gets too small, these relax (soft constraint). Other moods apply their own category preferences.
Rank & trim — All remaining places are ranked by their final score, then only the top K (30–50) are kept as the candidate pool for day packing.
3. Step B - Greedy Day Packing (Budget-aware)
How places are assigned to each day, one day at a time:

Initialize — Set budget_remaining = daily_budget_vnd, empty selected list, reference the global used_place_ids set.
Greedy loop — From remaining candidates, always pick the one with highest (finalScore / cost) ratio (best value).
Three checks per pick:
Does it fit in the remaining budget? If no → skip.
Already have 5 places today? If yes → day is done.
Already have 2 places of the same category today? If yes → skip (diversity rule).
If it passes all checks → add to the day, subtract cost from budget, mark as used globally.
Repeat for next day — The next day starts fresh with its own budget but the used_place_ids carries over, so no place appears twice across the trip.
4. Step C - Route Optimization
After day packing decides which places go on each day, this step decides what order to visit them:

Compute pairwise Haversine distances between all places selected for this day.
Nearest-neighbor starting from start_location (default: Hồ Gươm) — always go to the closest unvisited place next.
Optional 2-opt improvement — Try swapping pairs of edges to see if total distance decreases. With ≤5 nodes this is extremely fast (only 10 possible swaps).
The example shows a concrete result: Start at Hồ Gươm → Place A (0.5km) → Place B (1.2km) → Place C (0.8km) → Place D (1.5km).
5. Mood Scoring Model
How moodScore(place, mood) is calculated — the core personalization engine:

4 scoring signals combined additively:

Category Bonus (+30) — Cafe category boosts CHILL_CAFE, nature boosts NATURE_EXPLORE, food spots boost FOOD_LOCAL.
Healing Score — Heavily weighted for RESET_HEALING (healing × 20), lightly for others (healing × 5).
Crowd Penalty — Heavily penalized for RESET_HEALING (-crowd × 15), lightly for others (-crowd × 3). Quiet places score higher for healing.
Rating Bonus — Universal across all moods (rating × 10). Good places are good for everyone.
Two modes:

Solo — Just uses moodScore(place, mood) directly with the user's single chosen mood.
Group — Combines scores across all moods weighted by mood_distribution. Example: if the group is 40% RESET_HEALING + 30% CHILL_CAFE + 20% FOOD_LOCAL + 10% NATURE_EXPLORE, the final score is the weighted sum.
6. Regeneration & Edit Behavior
How the user interacts with the AI after initial generation:

"Generate Itinerary" — Runs the full A→B→C→D pipeline from scratch.
"Re-generate" — Same as generate but clears the previous plan first. In group mode, only the owner can do this.
"Manual Edit" (add/remove a stop) — Goes directly to the database. No auto-regenerate. The user's manual changes are preserved.
"Improve route only" (nice-to-have) — Runs only Step C (route optimization) on the existing places. Keeps the same places, just reorders them for shorter travel distance.
All paths end at Save → Display, which shows the updated plan with budget messaging (spent_today, remaining_today, saved_vs_budget) and any fallback warnings (e.g., "limited healing places available").