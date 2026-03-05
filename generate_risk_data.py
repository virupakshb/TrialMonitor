"""
Site Risk Ranking Data Generation Script
Protocol: NVX-1218.22 (NovaPlex-450 in Advanced NSCLC)
Sponsor: NexaVance Therapeutics Inc.

Adds 45 new sites (106-150), ~130 new subjects, and generates
3-month risk snapshots for all 50 sites.

Existing sites preserved: 101-105
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta, date

random.seed(1218)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinical_trial.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")  # allow inserts without full cascade
    return conn

# ─────────────────────────────────────────────────────────────────────────────
# SITE DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

EXISTING_SITE_REGIONS = {
    "101": ("North America", "Cancer Center"),
    "102": ("Europe", "Research Institute"),
    "103": ("North America", "Academic Medical Center"),
    "104": ("Asia Pacific", "Cancer Center"),
    "105": ("Asia Pacific", "Research Institute"),
}

NEW_SITES = [
    # USA (106-115)
    ("106", "Philadelphia Cancer Research Center", "United States", "Philadelphia", "PA", "North America", "Academic Medical Center", "Dr. Robert Kim", 20),
    ("107", "Houston Oncology Institute", "United States", "Houston", "TX", "North America", "Cancer Center", "Dr. Maria Santos", 25),
    ("108", "Northwestern Medical Center", "United States", "Chicago", "IL", "North America", "Academic Medical Center", "Dr. Andrew Liu", 22),
    ("109", "UCLA Hematology & Oncology", "United States", "Los Angeles", "CA", "North America", "Academic Medical Center", "Dr. Jennifer Park", 20),
    ("110", "NYU Langone Cancer Center", "United States", "New York", "NY", "North America", "Cancer Center", "Dr. Thomas Reyes", 22),
    ("111", "Fred Hutchinson Cancer Center", "United States", "Seattle", "WA", "North America", "Research Institute", "Dr. Sarah Mitchell", 18),
    ("112", "Sylvester Comprehensive Cancer Center", "United States", "Miami", "FL", "North America", "Academic Medical Center", "Dr. Carlos Mendez", 18),
    ("113", "Thomas Jefferson University Hospital", "United States", "Philadelphia", "PA", "North America", "Community Hospital", "Dr. Lisa Wong", 15),
    ("114", "UCHealth University of Colorado", "United States", "Denver", "CO", "North America", "Academic Medical Center", "Dr. Brian Foster", 15),
    ("115", "Banner MD Anderson Cancer Center", "United States", "Phoenix", "AZ", "North America", "Cancer Center", "Dr. Rachel Thompson", 15),
    # Canada (116-118)
    ("116", "BC Cancer Agency", "Canada", "Vancouver", "BC", "North America", "Cancer Center", "Dr. Helen Zhao", 20),
    ("117", "McGill University Health Centre", "Canada", "Montreal", "QC", "North America", "Academic Medical Center", "Dr. Pierre Dubois", 18),
    ("118", "Tom Baker Cancer Centre", "Canada", "Calgary", "AB", "North America", "Cancer Center", "Dr. Karen Nielsen", 15),
    # UK (119-121)
    ("119", "Christie Hospital NHS Trust", "United Kingdom", "Manchester", "England", "Europe", "Academic Medical Center", "Dr. James Thornton", 22),
    ("120", "Queen Elizabeth Hospital Birmingham", "United Kingdom", "Birmingham", "England", "Europe", "Community Hospital", "Dr. Fiona Clarke", 18),
    ("121", "Edinburgh Cancer Centre", "United Kingdom", "Edinburgh", "Scotland", "Europe", "Cancer Center", "Dr. Alistair Murray", 15),
    # Germany (122-126)
    ("122", "Charite Universitatsmedizin Berlin", "Germany", "Berlin", "", "Europe", "Academic Medical Center", "Dr. Klaus Weber", 25),
    ("123", "Ludwig Maximilian University Hospital", "Germany", "Munich", "", "Europe", "Academic Medical Center", "Dr. Hans Fischer", 22),
    ("124", "Universitatsklinikum Hamburg-Eppendorf", "Germany", "Hamburg", "", "Europe", "Academic Medical Center", "Dr. Ursula Braun", 20),
    ("125", "Goethe University Hospital Frankfurt", "Germany", "Frankfurt", "", "Europe", "Research Institute", "Dr. Markus Bauer", 18),
    ("126", "University Hospital Cologne", "Germany", "Cologne", "", "Europe", "Academic Medical Center", "Dr. Sabine Koch", 15),
    # France (127-130)
    ("127", "Institut Gustave Roussy", "France", "Paris", "", "Europe", "Cancer Center", "Dr. Sophie Laurent", 22),
    ("128", "Centre Leon Berard Lyon", "France", "Lyon", "", "Europe", "Cancer Center", "Dr. Jean-Pierre Martin", 18),
    ("129", "Institut Paoli-Calmettes Marseille", "France", "Marseille", "", "Europe", "Research Institute", "Dr. Anne Dupont", 15),
    ("130", "Institut Bergonie Bordeaux", "France", "Bordeaux", "", "Europe", "Cancer Center", "Dr. Marc Leroy", 12),
    # Spain (131-133)
    ("131", "Hospital Universitario La Paz", "Spain", "Madrid", "", "Europe", "Academic Medical Center", "Dr. Elena Fernandez", 20),
    ("132", "Hospital Clinic de Barcelona", "Spain", "Barcelona", "", "Europe", "Research Institute", "Dr. Ramon Guitart", 18),
    ("133", "Hospital Universitario La Fe Valencia", "Spain", "Valencia", "", "Europe", "Community Hospital", "Dr. Isabel Torres", 15),
    # Italy (134-136)
    ("134", "Istituto Nazionale dei Tumori Milano", "Italy", "Milan", "", "Europe", "Cancer Center", "Dr. Marco Rossi", 18),
    ("135", "Policlinico Universitario Gemelli", "Italy", "Rome", "", "Europe", "Academic Medical Center", "Dr. Giulia Bianchi", 15),
    ("136", "AOU Citta della Salute Torino", "Italy", "Turin", "", "Europe", "Academic Medical Center", "Dr. Antonio Ferrari", 12),
    # Japan (137-140)
    ("137", "National Cancer Center Hospital Tokyo", "Japan", "Tokyo", "", "Asia Pacific", "Cancer Center", "Dr. Kenji Tanaka", 22),
    ("138", "Nagoya University Hospital", "Japan", "Nagoya", "", "Asia Pacific", "Academic Medical Center", "Dr. Hiroshi Yamamoto", 18),
    ("139", "Osaka University Hospital", "Japan", "Osaka", "", "Asia Pacific", "Academic Medical Center", "Dr. Yuki Nakamura", 15),
    ("140", "Yokohama City University Hospital", "Japan", "Yokohama", "", "Asia Pacific", "Community Hospital", "Dr. Akiko Suzuki", 12),
    # South Korea (141-143)
    ("141", "Samsung Medical Center Seoul", "South Korea", "Seoul", "", "Asia Pacific", "Academic Medical Center", "Dr. Ji-Yeon Kim", 20),
    ("142", "Pusan National University Hospital", "South Korea", "Busan", "", "Asia Pacific", "Academic Medical Center", "Dr. Sung-Ho Lee", 15),
    ("143", "Inha University Hospital Incheon", "South Korea", "Incheon", "", "Asia Pacific", "Community Hospital", "Dr. Min-Ji Park", 12),
    # Australia (144-145)
    ("144", "Peter MacCallum Cancer Centre", "Australia", "Melbourne", "VIC", "Asia Pacific", "Cancer Center", "Dr. Catherine Brown", 18),
    ("145", "Princess Alexandra Hospital", "Australia", "Brisbane", "QLD", "Asia Pacific", "Community Hospital", "Dr. Michael Collins", 15),
    # Brazil (146-148)
    ("146", "Instituto do Cancer do Estado de Sao Paulo", "Brazil", "Sao Paulo", "", "Rest of World", "Cancer Center", "Dr. Ana Costa", 20),
    ("147", "INCA Rio de Janeiro", "Brazil", "Rio de Janeiro", "", "Rest of World", "Research Institute", "Dr. Paulo Silva", 15),
    ("148", "Hospital das Forcas Armadas Brasilia", "Brazil", "Brasilia", "", "Rest of World", "Community Hospital", "Dr. Claudia Oliveira", 12),
    # India (149-150)
    ("149", "Tata Memorial Hospital Mumbai", "India", "Mumbai", "", "Rest of World", "Cancer Center", "Dr. Rajesh Patel", 18),
    ("150", "Kidwai Memorial Institute Bangalore", "India", "Bangalore", "", "Rest of World", "Cancer Center", "Dr. Pradeep Nair", 15),
]

# ─────────────────────────────────────────────────────────────────────────────
# RISK ARCHETYPES  (site_id → {month: total_score})
# ─────────────────────────────────────────────────────────────────────────────

RISK_TRENDS = {
    # CRITICAL (rank 1) - 3 sites
    "101": {"202409": 65, "202410": 62, "202411": 58},   # improving, still critical
    "122": {"202409": 50, "202410": 53, "202411": 55},   # stable-high
    "138": {"202409": 40, "202410": 44, "202411": 52},   # deteriorating → critical

    # HIGH (rank 2) - 5 sites
    "103": {"202409": 38, "202410": 40, "202411": 41},   # stable high
    "107": {"202409": 44, "202410": 42, "202411": 41},   # slightly improving
    "119": {"202409": 25, "202410": 35, "202411": 43},   # DEMO: deteriorating fast
    "131": {"202409": 39, "202410": 38, "202411": 40},   # stable
    "141": {"202409": 36, "202410": 38, "202411": 41},   # slowly worsening

    # ELEVATED (rank 3) - 7 sites
    "102": {"202409": 32, "202410": 30, "202411": 33},
    "108": {"202409": 28, "202410": 31, "202411": 35},
    "123": {"202409": 30, "202410": 32, "202411": 34},
    "127": {"202409": 33, "202410": 31, "202411": 30},
    "132": {"202409": 29, "202410": 30, "202411": 32},
    "137": {"202409": 27, "202410": 29, "202411": 31},
    "146": {"202409": 25, "202410": 28, "202411": 30},

    # MODERATE (rank 4) - 10 sites
    "104": {"202409": 24, "202410": 22, "202411": 25},
    "109": {"202409": 20, "202410": 23, "202411": 24},
    "110": {"202409": 22, "202410": 21, "202411": 22},
    "120": {"202409": 21, "202410": 22, "202411": 23},
    "124": {"202409": 19, "202410": 21, "202411": 22},
    "128": {"202409": 23, "202410": 22, "202411": 20},
    "133": {"202409": 18, "202410": 20, "202411": 21},
    "139": {"202409": 20, "202410": 19, "202411": 22},
    "142": {"202409": 21, "202410": 23, "202411": 21},
    "147": {"202409": 19, "202410": 20, "202411": 20},

    # LOW (rank 5) - 10 sites
    "105": {"202409": 14, "202410": 12, "202411": 13},
    "111": {"202409": 15, "202410": 14, "202411": 12},
    "112": {"202409": 11, "202410": 13, "202411": 14},
    "121": {"202409": 12, "202410": 13, "202411": 13},
    "125": {"202409": 14, "202410": 13, "202411": 11},
    "129": {"202409": 10, "202410": 11, "202411": 13},
    "134": {"202409": 13, "202410": 12, "202411": 12},
    "143": {"202409": 11, "202410": 10, "202411": 11},
    "144": {"202409": 12, "202410": 14, "202411": 13},
    "148": {"202409": 10, "202410": 11, "202411": 10},

    # MINIMAL (rank 6) - 15 sites
    "106": {"202409": 5, "202410": 6, "202411": 5},
    "113": {"202409": 7, "202410": 5, "202411": 6},
    "114": {"202409": 4, "202410": 5, "202411": 4},
    "115": {"202409": 6, "202410": 4, "202411": 5},
    "116": {"202409": 3, "202410": 4, "202411": 5},
    "117": {"202409": 5, "202410": 6, "202411": 7},
    "118": {"202409": 4, "202410": 5, "202411": 6},
    "126": {"202409": 3, "202410": 4, "202411": 4},
    "130": {"202409": 6, "202410": 5, "202411": 5},
    "135": {"202409": 4, "202410": 3, "202411": 4},
    "136": {"202409": 5, "202410": 6, "202411": 5},
    "140": {"202409": 4, "202410": 5, "202411": 4},
    "145": {"202409": 3, "202410": 4, "202411": 5},
    "149": {"202409": 7, "202410": 6, "202411": 7},
    "150": {"202409": 5, "202410": 6, "202411": 6},
}

def assign_risk_rank(score):
    if score >= 50: return 1, "CRITICAL"
    if score >= 40: return 2, "HIGH"
    if score >= 30: return 3, "ELEVATED"
    if score >= 20: return 4, "MODERATE"
    if score >= 10: return 5, "LOW"
    return 6, "MINIMAL"

def calculate_trend(curr, prev):
    delta = curr - prev
    if delta > 5: return "DETERIORATING", delta
    if delta < -5: return "IMPROVING", delta
    return "STABLE", delta

RECOMMENDED_ACTIONS = {
    1: "IMMEDIATE: On-site visit within 7 days. Senior management escalation required.",
    2: "ACTION REQUIRED: Schedule on-site visit within 14 days. Weekly check-in calls.",
    3: "ENHANCED MONITORING: Remote visit next month. Review flagged items.",
    4: "STANDARD MONITORING: Continue schedule. Monitor watchlist items.",
    5: "ROUTINE MONITORING: Quarterly remote review.",
    6: "CONTINUE ROUTINE: Centralized monitoring only.",
}

def decompose_score(total, site_id, month):
    """Split a total risk score into realistic component scores."""
    rng = random.Random(int(site_id) * 100 + int(month))
    rank, _ = assign_risk_rank(total)

    if rank == 1:  # CRITICAL — all components elevated
        monitoring  = rng.randint(12, 20)
        pi          = rng.randint(10, 20)
        recruitment = rng.randint(10, 20)
        signal      = rng.randint(8, 15)
        qa          = rng.randint(6, 10)
    elif rank == 2:  # HIGH
        monitoring  = rng.randint(8, 15)
        pi          = rng.randint(8, 15)
        recruitment = rng.randint(8, 15)
        signal      = rng.randint(5, 12)
        qa          = rng.randint(4, 8)
    elif rank == 3:  # ELEVATED
        monitoring  = rng.randint(5, 12)
        pi          = rng.randint(5, 12)
        recruitment = rng.randint(5, 12)
        signal      = rng.randint(3, 8)
        qa          = rng.randint(2, 6)
    elif rank == 4:  # MODERATE
        monitoring  = rng.randint(3, 8)
        pi          = rng.randint(3, 8)
        recruitment = rng.randint(3, 8)
        signal      = rng.randint(2, 5)
        qa          = rng.randint(1, 4)
    elif rank == 5:  # LOW
        monitoring  = rng.randint(2, 6)
        pi          = rng.randint(1, 5)
        recruitment = rng.randint(2, 6)
        signal      = rng.randint(0, 4)
        qa          = rng.randint(0, 3)
    else:  # MINIMAL
        monitoring  = rng.randint(0, 3)
        pi          = rng.randint(0, 3)
        recruitment = rng.randint(0, 3)
        signal      = rng.randint(0, 2)
        qa          = rng.randint(0, 2)

    # Scale components to match total
    raw_sum = monitoring + pi + recruitment + signal + qa
    if raw_sum == 0:
        return 0, 0, 0, 0, 0

    scale = total / raw_sum
    monitoring  = min(20, round(monitoring  * scale))
    pi          = min(20, round(pi          * scale))
    recruitment = min(20, round(recruitment * scale))
    signal      = min(15, round(signal      * scale))
    qa          = min(10, round(qa          * scale))

    # Fix rounding drift
    diff = total - (monitoring + pi + recruitment + signal + qa)
    monitoring = max(0, monitoring + diff)

    return monitoring, pi, recruitment, signal, qa

def make_flags(site_id, month, total_score):
    """Generate boolean risk flags consistent with the score."""
    rng = random.Random(int(site_id) * 200 + int(month))
    rank, _ = assign_risk_rank(total_score)

    def flag(prob): return 1 if rng.random() < prob else 0

    if rank == 1:
        return {
            "sdv_backlog_flag":                1,
            "cra_turnover_flag":               flag(0.8),
            "pi_oversight_flag":               1,
            "enrollment_below_target_flag":    1,
            "non_enroller_flag":               flag(0.6),
            "high_sae_rate_flag":              flag(0.7),
            "protocol_deviation_critical_flag":1,
            "overdue_action_items_flag":       1,
            "high_query_rate_flag":            1,
            "consent_process_flag":            flag(0.5),
        }
    elif rank == 2:
        return {
            "sdv_backlog_flag":                flag(0.7),
            "cra_turnover_flag":               flag(0.5),
            "pi_oversight_flag":               flag(0.6),
            "enrollment_below_target_flag":    flag(0.7),
            "non_enroller_flag":               flag(0.3),
            "high_sae_rate_flag":              flag(0.4),
            "protocol_deviation_critical_flag":flag(0.6),
            "overdue_action_items_flag":       flag(0.7),
            "high_query_rate_flag":            flag(0.5),
            "consent_process_flag":            flag(0.3),
        }
    elif rank == 3:
        return {
            "sdv_backlog_flag":                flag(0.5),
            "cra_turnover_flag":               flag(0.3),
            "pi_oversight_flag":               flag(0.4),
            "enrollment_below_target_flag":    flag(0.5),
            "non_enroller_flag":               flag(0.1),
            "high_sae_rate_flag":              flag(0.2),
            "protocol_deviation_critical_flag":flag(0.3),
            "overdue_action_items_flag":       flag(0.5),
            "high_query_rate_flag":            flag(0.4),
            "consent_process_flag":            flag(0.2),
        }
    else:
        return {
            "sdv_backlog_flag":                flag(0.2),
            "cra_turnover_flag":               flag(0.1),
            "pi_oversight_flag":               flag(0.1),
            "enrollment_below_target_flag":    flag(0.3),
            "non_enroller_flag":               0,
            "high_sae_rate_flag":              flag(0.05),
            "protocol_deviation_critical_flag":flag(0.1),
            "overdue_action_items_flag":       flag(0.2),
            "high_query_rate_flag":            flag(0.1),
            "consent_process_flag":            0,
        }

def make_metrics(site_id, month, total_score, planned_enrollment):
    """Generate site metrics consistent with the risk score."""
    rng = random.Random(int(site_id) * 300 + int(month))
    rank, _ = assign_risk_rank(total_score)

    if rank == 1:
        active_subjects       = rng.randint(3, 12)
        days_since_visit      = rng.randint(45, 120)
        sae_rate              = round(rng.uniform(15, 28), 1)
        major_devs            = rng.randint(8, 20)
        overdue_ai            = rng.randint(15, 30)
        total_ai              = rng.randint(30, 50)
        avg_daily_crf         = round(rng.uniform(2, 6), 1)
        query_rate            = round(rng.uniform(25, 50), 1)
        screen_fail_rate      = round(rng.uniform(20, 35), 1)
    elif rank == 2:
        active_subjects       = rng.randint(5, 18)
        days_since_visit      = rng.randint(30, 60)
        sae_rate              = round(rng.uniform(10, 18), 1)
        major_devs            = rng.randint(4, 10)
        overdue_ai            = rng.randint(8, 18)
        total_ai              = rng.randint(20, 35)
        avg_daily_crf         = round(rng.uniform(5, 9), 1)
        query_rate            = round(rng.uniform(15, 28), 1)
        screen_fail_rate      = round(rng.uniform(15, 30), 1)
    elif rank == 3:
        active_subjects       = rng.randint(8, 22)
        days_since_visit      = rng.randint(20, 45)
        sae_rate              = round(rng.uniform(8, 14), 1)
        major_devs            = rng.randint(2, 6)
        overdue_ai            = rng.randint(4, 10)
        total_ai              = rng.randint(12, 25)
        avg_daily_crf         = round(rng.uniform(7, 12), 1)
        query_rate            = round(rng.uniform(10, 20), 1)
        screen_fail_rate      = round(rng.uniform(10, 22), 1)
    elif rank == 4:
        active_subjects       = rng.randint(10, 20)
        days_since_visit      = rng.randint(15, 35)
        sae_rate              = round(rng.uniform(6, 11), 1)
        major_devs            = rng.randint(1, 4)
        overdue_ai            = rng.randint(2, 6)
        total_ai              = rng.randint(8, 18)
        avg_daily_crf         = round(rng.uniform(9, 14), 1)
        query_rate            = round(rng.uniform(6, 14), 1)
        screen_fail_rate      = round(rng.uniform(8, 16), 1)
    elif rank == 5:
        active_subjects       = rng.randint(8, 18)
        days_since_visit      = rng.randint(10, 28)
        sae_rate              = round(rng.uniform(4, 9), 1)
        major_devs            = rng.randint(0, 2)
        overdue_ai            = rng.randint(0, 3)
        total_ai              = rng.randint(4, 12)
        avg_daily_crf         = round(rng.uniform(10, 16), 1)
        query_rate            = round(rng.uniform(4, 10), 1)
        screen_fail_rate      = round(rng.uniform(6, 12), 1)
    else:  # MINIMAL
        active_subjects       = rng.randint(2, 12)
        days_since_visit      = rng.randint(5, 21)
        sae_rate              = round(rng.uniform(0, 6), 1)
        major_devs            = 0
        overdue_ai            = rng.randint(0, 1)
        total_ai              = rng.randint(2, 8)
        avg_daily_crf         = round(rng.uniform(12, 22), 1)
        query_rate            = round(rng.uniform(1, 6), 1)
        screen_fail_rate      = round(rng.uniform(4, 10), 1)

    return {
        "active_subjects":         active_subjects,
        "days_since_last_visit":   days_since_visit,
        "sae_rate_pct":            sae_rate,
        "major_deviations_count":  major_devs,
        "overdue_action_items":    overdue_ai,
        "total_action_items":      total_ai,
        "avg_daily_crf_submissions": avg_daily_crf,
        "data_query_rate_pct":     query_rate,
        "screen_failure_rate_pct": screen_fail_rate,
    }

# ─────────────────────────────────────────────────────────────────────────────
# SUBJECT COUNTS PER NEW SITE
# ─────────────────────────────────────────────────────────────────────────────

NEW_SITE_SUBJECT_COUNTS = {
    "106": 2, "107": 10, "108": 7, "109": 4, "110": 4,
    "111": 3, "112": 3, "113": 2, "114": 2, "115": 2,
    "116": 3, "117": 3, "118": 2,
    "119": 9, "120": 4, "121": 3,
    "122": 7, "123": 6, "124": 3, "125": 3, "126": 2,
    "127": 5, "128": 3, "129": 2, "130": 2,
    "131": 8, "132": 5, "133": 3,
    "134": 3, "135": 2, "136": 2,
    "137": 6, "138": 5, "139": 3, "140": 2,
    "141": 6, "142": 3, "143": 2,
    "144": 3, "145": 2,
    "146": 5, "147": 3, "148": 2,
    "149": 3, "150": 2,
}
# Total new subjects: sum = 149


def random_date(start, end, rng=None):
    if rng is None:
        rng = random
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, max(0, delta)))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def run():
    conn = get_conn()
    cur = conn.cursor()

    print("=" * 60)
    print("SITE RISK DATA GENERATION — NVX-1218.22")
    print("=" * 60)

    # ── 1. Add region / site_type columns to sites (if not already there) ──
    print("\n[1/7] Checking region/site_type columns on sites table...")
    existing_cols = [r[1] for r in cur.execute("PRAGMA table_info(sites)").fetchall()]
    if "region" not in existing_cols:
        cur.execute("ALTER TABLE sites ADD COLUMN region TEXT")
        print("  Added: region")
    else:
        print("  OK: region already exists")
    if "site_type" not in existing_cols:
        cur.execute("ALTER TABLE sites ADD COLUMN site_type TEXT")
        print("  Added: site_type")
    else:
        print("  OK: site_type already exists")

    # ── 2. Update existing sites with region / type ───────────────────────
    print("\n[2/7] Updating existing sites with region/type...")
    for site_id, (region, site_type) in EXISTING_SITE_REGIONS.items():
        cur.execute(
            "UPDATE sites SET region=?, site_type=? WHERE site_id=?",
            (region, site_type, site_id)
        )
    print(f"  Updated {len(EXISTING_SITE_REGIONS)} existing sites")

    # ── 3. Insert new sites ───────────────────────────────────────────────
    print("\n[3/7] Inserting 45 new sites (106–150)...")
    site_rng = random.Random(1218)
    inserted_sites = 0
    for (sid, name, country, city, state, region, site_type, pi, planned) in NEW_SITES:
        existing = cur.execute("SELECT 1 FROM sites WHERE site_id=?", (sid,)).fetchone()
        if existing:
            continue
        activation = random_date(date(2023, 1, 15), date(2023, 6, 30), site_rng)
        cur.execute("""
            INSERT INTO sites (site_id, site_name, country, city, state_province,
                principal_investigator, activation_date, site_status,
                planned_enrollment, actual_enrollment, region, site_type)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (sid, name, country, city, state, pi,
              activation.isoformat(), "Active", planned, 0, region, site_type))
        inserted_sites += 1
    print(f"  Inserted {inserted_sites} new sites")

    # ── 4. Create risk tables ─────────────────────────────────────────────
    print("\n[4/7] Creating risk tables...")
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS site_risk_monthly_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id TEXT NOT NULL,
            month_end INTEGER NOT NULL,
            snapshot_date TEXT NOT NULL,
            monitoring_risk_score INTEGER DEFAULT 0,
            pi_risk_score INTEGER DEFAULT 0,
            recruitment_risk_score INTEGER DEFAULT 0,
            signal_risk_points INTEGER DEFAULT 0,
            qa_status_risk_pts INTEGER DEFAULT 0,
            total_risk_score INTEGER DEFAULT 0,
            risk_rank INTEGER,
            risk_level TEXT,
            trend_vs_prior TEXT,
            trend_delta INTEGER DEFAULT 0,
            sdv_backlog_flag INTEGER DEFAULT 0,
            cra_turnover_flag INTEGER DEFAULT 0,
            pi_oversight_flag INTEGER DEFAULT 0,
            enrollment_below_target_flag INTEGER DEFAULT 0,
            non_enroller_flag INTEGER DEFAULT 0,
            high_sae_rate_flag INTEGER DEFAULT 0,
            protocol_deviation_critical_flag INTEGER DEFAULT 0,
            overdue_action_items_flag INTEGER DEFAULT 0,
            high_query_rate_flag INTEGER DEFAULT 0,
            consent_process_flag INTEGER DEFAULT 0,
            active_subjects INTEGER DEFAULT 0,
            days_since_last_visit INTEGER DEFAULT 0,
            sae_rate_pct REAL DEFAULT 0,
            major_deviations_count INTEGER DEFAULT 0,
            overdue_action_items INTEGER DEFAULT 0,
            total_action_items INTEGER DEFAULT 0,
            avg_daily_crf_submissions REAL DEFAULT 0,
            data_query_rate_pct REAL DEFAULT 0,
            screen_failure_rate_pct REAL DEFAULT 0,
            recommended_action TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(site_id, month_end)
        );

        CREATE INDEX IF NOT EXISTS idx_risk_site ON site_risk_monthly_snapshot(site_id);
        CREATE INDEX IF NOT EXISTS idx_risk_month ON site_risk_monthly_snapshot(month_end);
        CREATE INDEX IF NOT EXISTS idx_risk_rank ON site_risk_monthly_snapshot(risk_rank);
    """)
    print("  Created: site_risk_monthly_snapshot")

    # ── 5. Generate risk snapshots ────────────────────────────────────────
    print("\n[5/7] Generating risk snapshots (3 months × 50 sites)...")
    months = ["202409", "202410", "202411"]
    snapshot_dates = {"202409": "2024-09-30", "202410": "2024-10-31", "202411": "2024-11-30"}

    # Get planned_enrollment for metrics
    enrollment_map = {r[0]: r[1] for r in
                      cur.execute("SELECT site_id, planned_enrollment FROM sites").fetchall()}

    inserted_snapshots = 0
    for site_id, monthly_scores in RISK_TRENDS.items():
        for i, month in enumerate(months):
            total = monthly_scores[month]
            rank, level = assign_risk_rank(total)

            # Trend vs prior month
            if i == 0:
                trend, delta = "STABLE", 0
            else:
                prior_month = months[i - 1]
                prior_total = monthly_scores[prior_month]
                trend, delta = calculate_trend(total, prior_total)

            m, p, r, s, q = decompose_score(total, site_id, month)
            flags = make_flags(site_id, month, total)
            metrics = make_metrics(site_id, month, total, enrollment_map.get(site_id, 20))

            cur.execute("DELETE FROM site_risk_monthly_snapshot WHERE site_id=? AND month_end=?",
                        (site_id, int(month)))
            cur.execute("""
                INSERT INTO site_risk_monthly_snapshot (
                    site_id, month_end, snapshot_date,
                    monitoring_risk_score, pi_risk_score, recruitment_risk_score,
                    signal_risk_points, qa_status_risk_pts,
                    total_risk_score, risk_rank, risk_level,
                    trend_vs_prior, trend_delta,
                    sdv_backlog_flag, cra_turnover_flag, pi_oversight_flag,
                    enrollment_below_target_flag, non_enroller_flag,
                    high_sae_rate_flag, protocol_deviation_critical_flag,
                    overdue_action_items_flag, high_query_rate_flag, consent_process_flag,
                    active_subjects, days_since_last_visit, sae_rate_pct,
                    major_deviations_count, overdue_action_items, total_action_items,
                    avg_daily_crf_submissions, data_query_rate_pct,
                    screen_failure_rate_pct, recommended_action
                ) VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
            """, (
                site_id, int(month), snapshot_dates[month],
                m, p, r, s, q,
                total, rank, level,
                trend, delta,
                flags["sdv_backlog_flag"], flags["cra_turnover_flag"], flags["pi_oversight_flag"],
                flags["enrollment_below_target_flag"], flags["non_enroller_flag"],
                flags["high_sae_rate_flag"], flags["protocol_deviation_critical_flag"],
                flags["overdue_action_items_flag"], flags["high_query_rate_flag"],
                flags["consent_process_flag"],
                metrics["active_subjects"], metrics["days_since_last_visit"], metrics["sae_rate_pct"],
                metrics["major_deviations_count"], metrics["overdue_action_items"],
                metrics["total_action_items"],
                metrics["avg_daily_crf_submissions"], metrics["data_query_rate_pct"],
                metrics["screen_failure_rate_pct"],
                RECOMMENDED_ACTIONS[rank]
            ))
            inserted_snapshots += 1

    print(f"  Inserted {inserted_snapshots} risk snapshots")

    # ── 6. Insert subjects for new sites ──────────────────────────────────
    print("\n[6/7] Inserting subjects for new sites...")
    inserted_subjects = 0
    screening_start = date(2023, 4, 1)
    screening_end   = date(2024, 10, 1)

    statuses_pool = ["Enrolled", "Enrolled", "Enrolled", "Completed", "Screen Failed", "Enrolled",
                     "Enrolled", "Completed", "Enrolled", "Discontinued"]

    for site_id, count in NEW_SITE_SUBJECT_COUNTS.items():
        # Check current max seq for this site
        existing_max = cur.execute(
            "SELECT subject_id FROM subjects WHERE site_id=? ORDER BY subject_id",
            (site_id,)
        ).fetchall()

        existing_seqs = set()
        for (subj_id,) in existing_max:
            parts = subj_id.split("-")
            if len(parts) == 2 and parts[1].isdigit():
                existing_seqs.add(int(parts[1]))

        subj_rng = random.Random(int(site_id) * 999)
        seq = 1
        site_inserted = 0

        for _ in range(count):
            while seq in existing_seqs:
                seq += 1
            subject_id = f"{site_id}-{seq:03d}"
            existing_seqs.add(seq)

            status = statuses_pool[subj_rng.randint(0, len(statuses_pool) - 1)]
            screening_date = random_date(screening_start, screening_end, subj_rng)
            consent_date = screening_date - timedelta(days=subj_rng.randint(0, 3))
            rand_date = screening_date + timedelta(days=subj_rng.randint(21, 42)) if status != "Screen Failed" else None
            treatment_arm = subj_rng.randint(1, 2) if status != "Screen Failed" else None
            arm_name = "NovaPlex-450 + Chemotherapy" if treatment_arm == 1 else ("Chemotherapy Alone" if treatment_arm == 2 else None)

            disc_date = None
            disc_reason = None
            if status == "Discontinued":
                disc_date = (rand_date + timedelta(days=subj_rng.randint(30, 180))).isoformat() if rand_date else None
                disc_reason = subj_rng.choice(["Adverse Event", "Withdrawal of Consent", "Progressive Disease"])

            cur.execute("""
                INSERT OR IGNORE INTO subjects (
                    subject_id, site_id, treatment_arm, treatment_arm_name,
                    randomization_date, screening_date, consent_date,
                    study_status, discontinuation_date, discontinuation_reason
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                subject_id, site_id, treatment_arm, arm_name,
                rand_date.isoformat() if rand_date else None,
                screening_date.isoformat(),
                consent_date.isoformat(),
                status,
                disc_date, disc_reason
            ))
            site_inserted += 1
            inserted_subjects += 1
            seq += 1

        # Update actual_enrollment for site
        enrolled_count = cur.execute(
            "SELECT COUNT(*) FROM subjects WHERE site_id=? AND study_status NOT IN ('Screen Failed')",
            (site_id,)
        ).fetchone()[0]
        cur.execute("UPDATE sites SET actual_enrollment=? WHERE site_id=?",
                    (enrolled_count, site_id))

    print(f"  Inserted {inserted_subjects} new subjects")

    # ── 7. Summary ────────────────────────────────────────────────────────
    conn.commit()
    conn.close()

    print("\n[7/7] Summary")
    print("-" * 60)
    conn2 = sqlite3.connect(DB_PATH)
    cur2 = conn2.cursor()

    total_sites    = cur2.execute("SELECT COUNT(*) FROM sites").fetchone()[0]
    total_subjects = cur2.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
    total_snapshots= cur2.execute("SELECT COUNT(*) FROM site_risk_monthly_snapshot").fetchone()[0]

    print(f"  Total sites:     {total_sites}")
    print(f"  Total subjects:  {total_subjects}")
    print(f"  Risk snapshots:  {total_snapshots}")

    print("\n  Risk distribution (Nov 2024):")
    rows = cur2.execute("""
        SELECT risk_level, COUNT(*) FROM site_risk_monthly_snapshot
        WHERE month_end=202411 GROUP BY risk_level ORDER BY risk_rank
    """).fetchall()
    for level, cnt in rows:
        print(f"    {level:12s} {cnt} sites")

    conn2.close()
    print("\nData generation complete.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        import traceback
        print("ERROR in generate_risk_data.py:")
        traceback.print_exc()
        # Exit 0 so uvicorn still starts; risk data simply won't be populated
        import sys
        sys.exit(0)
