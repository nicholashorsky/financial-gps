# Financial GPS — Project Status Assessment
**Date:** 2026-07-21
**Methodology:** `vibe_coding_prompt.md` (Idea State → Spec State → Build State)
**Repo assessed:** [github.com/nicholashorsky/financial-gps](https://github.com/nicholashorsky/financial-gps) (main, 7 commits, 99.9% Python)
**Docs assessed against:** `Financial_GPS_Project_Vision.md` · `firecanadianresearchreport.md` · `financial_gps_unified_spec.md`

---

## 1. Where this sits in the 3-state model

| State | Artifact | Status |
|---|---|---|
| Idea State | `Financial_GPS_Project_Vision.md` | ✅ Superseded — folded into the unified spec |
| Idea State (domain deep-dive) | `firecanadianresearchreport.md` | ✅ Superseded — folded into the unified spec's Canadian FIRE sections |
| Spec State | `financial_gps_unified_spec.md` | ✅ Current, versioned 2.0, includes data model + 8-phase build plan |
| Build State | GitHub repo (`nicholashorsky/financial-gps`) | 🟡 In progress — matches spec through Phase 7, Phase 8 actively underway (matches README's own claim) |

The spec is unusually strong for this stage: it already carries a real data model, screen list, and phased build plan, so this assessment is a straight diff against Section 15 of `financial_gps_unified_spec.md` (MVP Build Plan) rather than a fresh spec.

---

## 2. Phase-by-phase diff (spec vs. code)

| Phase | Spec says | Code reality |
|---|---|---|
| **0 — Foundation** | Schema, auth, nav skeleton, CRA 2026 params, quarterly loader | ✅ Done. `shared/db.py` has all budget + FIRE tables; `auth/` has bcrypt login/register; `cra_2026.py` matches the T4032-ON gold values exactly. ⚠️ `cra_2024.py`/`cra_2025.py` are referenced in the folder plan but don't exist — `loader.py` silently no-ops for `year != 2026` |
| **1 — Budget: Data In** | RBC/CC parser, categorizer, transfer detector, ghost accounts | ✅ Done. Categorizer ships ~90 keyword rules (spec asked for 50+) |
| **1b — Transaction Intelligence** | Split/cash/offset engines, bridge first run | ✅ Done, but see gap #3 below (duplicate offset logic) |
| **2 — Dashboards** | Spending, Home, Goals, basic Forecast, narrator | ✅ Done, and Home already includes the FIRE Date KPI card the spec scheduled for Phase 6 |
| **3 — What-If Engine** | 4 scenario calculators + UI | ✅ Done |
| **4 — FIRE L1 Engine (gate)** | Room calculators, CRA-regression-tested tax engine, CPP/OAS/GIS, decumulation, 40-yr loop | ✅ Gate passed — both CRA regression cases match exactly in `test_federal_tax.py` / `test_provincial_tax_on.py`. See gaps #1–#2 below for real shortfalls hiding behind the passing tests |
| **5 — FIRE UI Screens** | Profile, room tracker, benefits, goal setup, forecast, data quality | ✅ All six screens exist and are wired into `app.py` nav |
| **6 — Scenarios + Bridge Polish** | Clone/compare engine, FIRE scenario UI, bridge notifications | ✅ Done |
| **7 — Polish + Onboarding** | Onboarding flow, empty states, settings, mobile audit | 🟡 Mostly done. Onboarding, empty states, and narrator library are complete. Mobile-first layout has **not** been explicitly audited (see gap #7) |
| **8 — Beta Hardening** | Sample CSV regression tests, deployment hygiene, fresh-account beta run | 🟡 In progress, matches README's own "Current: Phase 8" claim. Sample CSV + bridge regression tests exist (`test_sample_csv_import.py`); a dev-only test-login shortcut has been added for beta testers (not yet reflected back in the spec — see gap #6) |

**Bottom line:** Phases 0–6 are functionally complete against the spec, Phase 7 is ~90%, and Phase 8 is honestly in-progress. The project is roughly where its own README says it is.

---

## 3. Gaps worth closing (ranked)

### High priority — affects forecast correctness
1. **RRIF conversion doesn't actually happen.** `fire_engine/engine/rules.py` fires an `"RRSP age-71 approaching"` string, but `projection.py` never forces a minimum RRIF withdrawal once the person crosses 71/72. The spec's own edge-case table promises *"Rule fires; projection converts to RRIF withdrawal."* Right now it's a warning label with no behavioral effect — a live accuracy gap in exactly the scenario `firecanadianresearchreport.md` calls out as mandatory.
2. **Decumulation isn't marginal-rate-aware.** `decumulation.py`'s docstring and the spec's folder plan both describe a *"marginal-rate-aware waterfall sequencer,"* but the implementation is a fixed order (`taxable → rrsp → tfsa → fhsa → hisa → rrif`) with no tax comparison logic. The research report specifically warns that a naive sequencer produces the *wrong* optimal withdrawal order for GIS-eligible or bracket-sensitive households — this is the single feature most likely to make a forecast quietly wrong.
3. **CPP is a flat assumed ratio.** `estimate_cpp_monthly` takes a hardcoded `0.7` pensionable-earnings ratio from the service layer rather than actual contribution history. Acceptable as a documented MVP simplification, but there's no UI path yet for a user to override it with their real Service Canada estimate beyond the Data Quality warning flag.

### Medium priority — cleanup / drift
4. **Duplicate offset logic.** `budget/cash_tracker.py` (`record_cash_offset` / `unlink_cash_offset`) and `budget/offset_engine.py` (`create_offset_pair` / `remove_offset_pair`) do the same job against the same `cash_offsets` table. Only `offset_engine` is exercised by the smoke test — `cash_tracker.py` looks like dead code from an earlier pass. Pick one and delete the other.
5. **Parameter loader stub.** `get_params(year != 2026, ...)` has a `pass` where 2024/2025 params should load. Either implement those modules or make the function raise clearly instead of silently returning 2026 numbers for other years.
6. **Spec/build drift.** The live repo has a dev-only test-login shortcut (`start_dev_app.bat`, `FINANCIAL_GPS_TEST_LOGIN` env var, described in the GitHub README) that isn't mentioned anywhere in `financial_gps_unified_spec.md`. Per the vibe_coding methodology, build-state additions like this should get folded back into the spec so the two don't diverge.
7. **Mobile audit is unverified.** The spec explicitly lists "mobile-first considerations" and a Phase 7 mobile audit, but the UI leans on 3–5-wide `st.columns()` layouts throughout (`fire_profile.py`, `home.py`, `fire_room_tracker.py`) with no evidence of a narrow-viewport pass.

### Low priority — correctly deferred, not urgent
8. Multi-province tax (BC/AB/QC), Quebec-native mode, pension splitting, Monte Carlo, Postgres/Supabase migration — all explicitly scoped to V1.5–V3 in the spec's roadmap, and the code correctly gates Quebec with a raised error rather than silently miscalculating. No action needed now.

---

## 4. Ahead of spec (good signals)

- Categorizer ships ~90 system keyword rules vs. the "50+" the spec asked for.
- Narrator message library already covers **both** budget and FIRE events, which the spec had staged across separate phases.
- Home dashboard's FIRE Date KPI (a Phase 6 item) is already live.
- Smoke test suite (`tests/smoke_test.py`) exercises nearly every service end-to-end, plus a dedicated real-sample-CSV regression test — stronger coverage than a typical "Phase 8 minimum."
- The dev test-login convenience is a good pragmatic addition for smoother beta testing, even though it needs to be folded back into the spec.

---

## 5. Recommended next steps

**Finish Phase 8 as scoped:**
1. Fold the dev test-login feature into `financial_gps_unified_spec.md` so spec and build stop diverging.
2. Delete or merge `cash_tracker.py` into `offset_engine.py`.
3. Run the actual "fresh account on deployed app" beta pass the README still lists as unchecked.

**Close the correctness gaps before trusting FIRE output:**
4. Implement real RRIF minimum-withdrawal behavior in `projection.py` once the age-71 rule fires.
5. Upgrade `decumulation.py` to compare next-dollar tax cost across account types before choosing a withdrawal source, instead of a fixed order.
6. Either implement `cra_2025.py`/historical params or make the loader fail loudly for unsupported years instead of silently reusing 2026 figures.

**Round out Phase 7:**
7. Do an explicit mobile-layout pass over every `st.columns()` call.
8. Expand Settings to cover the "tax assumptions" the spec promises beyond FIRE variant/spending floor-ceiling.
9. Add a manual CPP-override input path so the "CPP estimate missing" Data Quality warning has a real resolution, not just a flag.

**No action needed yet (correctly deferred):** multi-province tax, Quebec-native mode, pension splitting, Monte Carlo simulation, Postgres/Supabase migration.

---

*Want me to turn items 4–6 (RRIF conversion, marginal-rate-aware decumulation, parameter loader) into a build-state engineering spec — data model deltas, function signatures, and test cases — so it's ready to hand straight to a coding session?*
