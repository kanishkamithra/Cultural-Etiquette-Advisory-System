from __future__ import annotations

import hashlib
import secrets
from pathlib import Path
from typing import Any

import pycountry
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pymysql.err import IntegrityError

from models.schemas import (
    AdviceRequest,
    CommunityTipIn,
    CompareRequest,
    CultureIn,
    FavoriteIn,
    FeedbackIn,
    LoginIn,
    MistakeAlertRequest,
    NlpAdviceRequest,
    RegisterIn,
    RuleIn,
    SaveAdviceIn,
    ScenarioIn,
    SessionOut,
    SimulationRequest,
    UserOut,
)
from services.db import (
    DB_NAME,
    execute,
    execute_many,
    fetch_all_dicts,
    fetch_one_dict,
    get_db,
    log_activity,
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

app = FastAPI(title="Cultural Etiquette Advisory System API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()



SCENARIO_SEEDS = [
    ("Greeting", "First impressions, introductions, and respectful openings."),
    ("Dining", "Meal etiquette, table behavior, and host interaction."),
    ("Business Meeting", "Professional etiquette for meetings, exchange, and timing."),
    ("Gift Giving", "Choosing, presenting, and receiving gifts appropriately."),
]


COUNTRY_OVERRIDES = {
    "Japan": {
        "summary": "High-context culture valuing respect, restraint, and social harmony.",
        "rules": {
            "Greeting": (
                "Offer a light bow and wait for the other person to initiate a handshake.",
                "Do not greet loudly or with exaggerated physical contact.",
                "Formality and modesty signal respect in first meetings.",
                "If unsure, smile, bow slightly, and use a polite verbal greeting.",
                "Important",
            ),
            "Dining": (
                "Wait for everyone to be served before starting and say a brief thanks before eating.",
                "Do not stick chopsticks upright in rice or point with them.",
                "Certain chopstick actions are associated with funerary customs and can feel offensive.",
                "If you are unsure about a custom, quietly copy the host's pace and table style.",
                "Important",
            ),
            "Business Meeting": (
                "Exchange business cards with both hands and take a moment to read the card.",
                "Do not put a received business card directly into a back pocket.",
                "Cards represent professional identity and should be handled carefully.",
                "If uncertain, place the card neatly on the table or in a card holder.",
                "Important",
            ),
        },
    },
    "United States": {
        "summary": "Direct communication style with emphasis on personal space and punctuality.",
        "rules": {
            "Greeting": (
                "Use a firm handshake, eye contact, and a concise introduction.",
                "Do not stand too close or ask highly personal questions immediately.",
                "Personal space and directness are common expectations.",
                "A simple hello with your name and role is a safe start.",
                "Advisory",
            ),
            "Dining": (
                "Tip service staff when dining in and follow the host for table cues.",
                "Do not begin controversial discussions if the setting is formal or unfamiliar.",
                "Dining can feel relaxed, but social and professional boundaries still matter.",
                "Keep conversation light and mirror the tone of the table.",
                "Advisory",
            ),
            "Business Meeting": (
                "Arrive on time and speak clearly about goals or next steps.",
                "Do not assume relationship-building alone can replace punctuality or preparation.",
                "Time awareness is often read as professionalism.",
                "If delayed, send a short update and apology before the meeting starts.",
                "Important",
            ),
        },
    },
    "United Arab Emirates": {
        "summary": "Relationship-focused etiquette with strong respect for hospitality and formality.",
        "rules": {
            "Greeting": (
                "Greet the most senior person first and use respectful titles.",
                "Do not rush into business before brief relationship-building conversation.",
                "Courtesy and relational trust are valued before transactional talk.",
                "Begin with a warm greeting and let the host guide the pace.",
                "Important",
            ),
            "Dining": (
                "Accept refreshments when offered and use the right hand for eating or passing items.",
                "Do not refuse hospitality abruptly or use the left hand for shared food interactions.",
                "Hospitality is a meaningful social gesture and hand use carries etiquette weight.",
                "If unsure, politely accept a small amount and observe others.",
                "Important",
            ),
            "Gift Giving": (
                "Choose modest, thoughtful gifts and present them respectfully.",
                "Do not give overly personal items or alcohol unless you are certain it is appropriate.",
                "Gift norms are shaped by formality and religious context.",
                "When unsure, bring quality sweets or a neutral office gift.",
                "Advisory",
            ),
        },
    },
    "India": {
        "summary": "Relationship-oriented etiquette where hierarchy, hospitality, and respect shape many interactions.",
        "rules": {
            "Greeting": (
                "Use a polite greeting such as Namaste or a light handshake depending on the setting, and greet elders or senior people first.",
                "Do not jump into overly casual first-name familiarity or public disagreement at the start of an interaction.",
                "Respectful openings and acknowledgement of seniority help build trust quickly in many Indian settings.",
                "Start warmly, use titles when appropriate, and let the other person set the level of informality.",
                "Important",
            ),
            "Dining": (
                "Wait for the host to begin, and be mindful that some households prefer eating or serving with the right hand.",
                "Do not criticize spice levels, dietary practices, or local food customs at the table.",
                "Meals often carry hospitality and family respect, so adaptability matters as much as manners.",
                "If unsure, accept a small serving first and politely ask how the host prefers the meal to proceed.",
                "Important",
            ),
            "Business Meeting": (
                "Allow time for rapport before pushing decisions, while still arriving prepared and on time.",
                "Do not mistake cordial conversation for lack of seriousness or interrupt senior participants.",
                "Many business interactions combine relationship-building with visible respect for hierarchy.",
                "Open with brief conversation, then move into agenda points once the tone is set.",
                "Advisory",
            ),
        },
    },
    "Germany": {
        "summary": "Direct but formal professional culture that values punctuality, preparation, and clear agreements.",
        "rules": {
            "Greeting": (
                "Use a brief handshake, steady eye contact, and surnames until invited to do otherwise.",
                "Do not arrive late or assume immediate informality with new contacts.",
                "Precision, punctuality, and professional distance are commonly read as respect.",
                "Lead with a concise introduction and match the room's level of formality.",
                "Important",
            ),
        },
    },
    "Brazil": {
        "summary": "Warm interpersonal style where friendliness and flexibility often matter alongside formality.",
        "rules": {
            "Greeting": (
                "Greet people warmly and be ready for a more personal conversational style than in highly formal cultures.",
                "Do not act cold, overly rushed, or dismissive of small talk.",
                "Friendliness helps establish comfort and trust before the practical discussion begins.",
                "Take a moment to connect personally before moving into business.",
                "Advisory",
            ),
        },
    },
}

REGIONAL_RULES = {
    "anglosphere": {
        "Greeting": (
            "Start with a clear greeting, moderate eye contact, and respectful personal space.",
            "Do not force intimacy, over-explain, or crowd the other person in a first meeting.",
            "Professional warmth is usually appreciated more than ceremony-heavy formality.",
            "Use a concise introduction and mirror the other person's tone.",
            "Advisory",
        ),
        "Dining": (
            "Follow host cues, keep conversation balanced, and watch the table pace before starting.",
            "Do not dominate the table, mock food preferences, or assume everyone shares the same boundaries.",
            "Dining etiquette often centers on politeness, timing, and keeping others comfortable.",
            "Stay observant, and keep your early behavior conservative until the tone is clear.",
            "Advisory",
        ),
    },
    "east_asia": {
        "Greeting": (
            "Begin with calm formality and pay attention to how the other person signals respect.",
            "Do not overuse touch, loud humor, or exaggerated gestures when first meeting.",
            "Restraint and careful observation often communicate professionalism and respect.",
            "Let the host's pace guide how formal the interaction should be.",
            "Important",
        ),
        "Business Meeting": (
            "Come prepared, be measured in disagreement, and respect the order of introductions in the room.",
            "Do not challenge someone bluntly in front of others or rush straight into debate.",
            "Meetings may value harmony, preparation, and status signals as much as speed.",
            "Frame questions carefully and offer disagreement in a constructive, low-friction way.",
            "Important",
        ),
    },
    "middle_east": {
        "Greeting": (
            "Open warmly, use titles, and allow respectful relationship-building before discussing business.",
            "Do not hurry the social opening or behave too casually with senior figures.",
            "Hospitality and personal respect often shape the quality of the interaction.",
            "Greet the senior person first and let the host guide the rhythm.",
            "Important",
        ),
        "Gift Giving": (
            "Choose modest gifts that fit the context and present them with discretion.",
            "Do not assume food, drink, or highly personal items are automatically appropriate.",
            "Religious and social expectations can shape what is suitable in a meaningful way.",
            "When uncertain, select a neutral high-quality gift and avoid anything intimate.",
            "Advisory",
        ),
    },
}

COUNTRY_GROUPS = {
    "anglosphere": {"United States", "United Kingdom", "Canada", "Australia", "New Zealand", "Ireland"},
    "east_asia": {"Japan", "China", "South Korea", "Singapore", "Taiwan", "Hong Kong"},
    "middle_east": {"United Arab Emirates", "Saudi Arabia", "Qatar", "Kuwait", "Oman", "Bahrain", "Jordan", "Egypt"},
}


def country_summary(country_name: str) -> str:
    override = COUNTRY_OVERRIDES.get(country_name, {})
    if override.get("summary"):
        return override["summary"]
    if country_name in COUNTRY_GROUPS["east_asia"]:
        return f"Etiquette guidance for {country_name} with emphasis on restraint, respectful pacing, and careful attention to hierarchy and group harmony."
    if country_name in COUNTRY_GROUPS["middle_east"]:
        return f"Etiquette guidance for {country_name} with emphasis on hospitality, formality, and relationship-building before moving too quickly into business."
    if country_name in COUNTRY_GROUPS["anglosphere"]:
        return f"Etiquette guidance for {country_name} with emphasis on clarity, personal space, and practical, respectful communication."
    return f"Etiquette guidance for {country_name}, focused on respectful observation, host cues, and adapting to local expectations in each situation."


def default_rule_bundle(country_name: str, scenario_name: str) -> tuple[str, str, str, str, str]:
    for group_name, countries in COUNTRY_GROUPS.items():
        if country_name in countries and scenario_name in REGIONAL_RULES[group_name]:
            return REGIONAL_RULES[group_name][scenario_name]

    defaults = {
        "Greeting": (
            f"In {country_name}, start with a polite verbal greeting and follow the other person's lead for handshakes or distance.",
            "Do not assume casual touch, first-name familiarity, or humor is always appropriate at the first meeting.",
            f"First impressions in {country_name} can depend on showing respect for formality, distance, and local expectations.",
            "Use a warm hello, maintain respectful body language, and mirror the host's tone.",
            "Advisory",
        ),
        "Dining": (
            f"In {country_name}, wait for host cues before starting, follow table etiquette, and thank the host when appropriate.",
            "Do not criticize local food habits or ignore seating and serving customs.",
            f"Meal settings in {country_name} often communicate respect, hospitality, and social awareness.",
            "If unsure, observe the pace of the host and choose conservative table behavior.",
            "Advisory",
        ),
        "Business Meeting": (
            f"In {country_name}, arrive prepared, greet participants respectfully, and keep your communication clear and professional.",
            "Do not interrupt repeatedly, dismiss hierarchy, or improvise without understanding meeting expectations.",
            f"Professional etiquette in {country_name} is shaped by local expectations around punctuality, hierarchy, and communication style.",
            "Bring a concise agenda, ask respectful questions, and adapt to the room's formality.",
            "Important",
        ),
        "Gift Giving": (
            f"In {country_name}, offer gifts thoughtfully and only when the setting clearly welcomes it.",
            "Do not give highly personal, overly expensive, or culturally sensitive items without checking appropriateness.",
            f"Gift norms in {country_name} can vary by occasion, status, and cultural symbolism.",
            "When unsure, choose a modest professional gift or handwritten note instead.",
            "Optional",
        ),
    }
    return defaults[scenario_name]


def refresh_seeded_content(connection) -> None:
    cultures = fetch_all_dicts(connection, "SELECT id, name, summary FROM cultures")
    scenarios = fetch_all_dicts(connection, "SELECT id, name FROM scenarios")
    scenario_map = {row["id"]: row["name"] for row in scenarios}

    for culture in cultures:
        if culture["summary"].startswith("Etiquette guidance for "):
            execute(
                connection,
                "UPDATE cultures SET summary = %s WHERE id = %s",
                (country_summary(culture["name"]), culture["id"]),
            )

    rules = fetch_all_dicts(
        connection,
        "SELECT id, culture_id, scenario_id, do_text, dont_text, reason, safe_alternative FROM rules",
    )
    culture_name_by_id = {row["id"]: row["name"] for row in cultures}

    for rule in rules:
        culture_name = culture_name_by_id.get(rule["culture_id"])
        scenario_name = scenario_map.get(rule["scenario_id"])
        if not culture_name or not scenario_name:
            continue
        if not (
            rule["do_text"].startswith(f"In {culture_name},")
            or rule["dont_text"].startswith("Do not assume")
            or rule["reason"].startswith(f"First impressions in {culture_name}")
            or rule["reason"].startswith(f"Meal settings in {culture_name}")
            or rule["reason"].startswith(f"Professional etiquette in {culture_name}")
            or rule["reason"].startswith(f"Gift norms in {culture_name}")
        ):
            continue
        rule_bundle = COUNTRY_OVERRIDES.get(culture_name, {}).get("rules", {}).get(
            scenario_name,
            default_rule_bundle(culture_name, scenario_name),
        )
        execute(
            connection,
            """
            UPDATE rules
            SET do_text = %s, dont_text = %s, reason = %s, safe_alternative = %s, severity = %s
            WHERE id = %s
            """,
            (*rule_bundle, rule["id"]),
        )


def seed_reference_data(connection) -> None:
    existing_cultures = {row["name"]: row for row in fetch_all_dicts(connection, "SELECT id, name FROM cultures")}
    country_rows = sorted(pycountry.countries, key=lambda item: item.name)
    cultures_to_create = [(country.name, country_summary(country.name)) for country in country_rows if country.name not in existing_cultures]
    if cultures_to_create:
        execute_many(connection, "INSERT INTO cultures (name, summary) VALUES (%s, %s)", cultures_to_create)

    existing_scenarios = {row["name"]: row for row in fetch_all_dicts(connection, "SELECT id, name FROM scenarios")}
    scenarios_to_create = [(name, description) for name, description in SCENARIO_SEEDS if name not in existing_scenarios]
    if scenarios_to_create:
        execute_many(connection, "INSERT INTO scenarios (name, description) VALUES (%s, %s)", scenarios_to_create)

    culture_map = {row["name"]: row["id"] for row in fetch_all_dicts(connection, "SELECT id, name FROM cultures")}
    scenario_map = {row["name"]: row["id"] for row in fetch_all_dicts(connection, "SELECT id, name FROM scenarios")}
    existing_rule_keys = {
        (row["culture_id"], row["scenario_id"]) for row in fetch_all_dicts(connection, "SELECT culture_id, scenario_id FROM rules")
    }

    rules_to_create: list[tuple[Any, ...]] = []
    for country in country_rows:
        for scenario_name, _ in SCENARIO_SEEDS:
            culture_id = culture_map[country.name]
            scenario_id = scenario_map[scenario_name]
            if (culture_id, scenario_id) in existing_rule_keys:
                continue
            rule_bundle = COUNTRY_OVERRIDES.get(country.name, {}).get("rules", {}).get(
                scenario_name,
                default_rule_bundle(country.name, scenario_name),
            )
            rules_to_create.append((culture_id, scenario_id, *rule_bundle))

    if rules_to_create:
        execute_many(
            connection,
            """
            INSERT INTO rules (culture_id, scenario_id, do_text, dont_text, reason, safe_alternative, severity)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            rules_to_create,
        )


def init_db() -> None:
    with get_db(include_database=False) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )

    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(120) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(64) NOT NULL,
                    role ENUM('user', 'admin') NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    token VARCHAR(128) PRIMARY KEY,
                    user_id INT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cultures (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(120) NOT NULL UNIQUE,
                    summary VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scenarios (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(120) NOT NULL UNIQUE,
                    description VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS rules (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    culture_id INT NOT NULL,
                    scenario_id INT NOT NULL,
                    do_text VARCHAR(500) NOT NULL,
                    dont_text VARCHAR(500) NOT NULL,
                    reason VARCHAR(500) NOT NULL,
                    safe_alternative VARCHAR(500) NOT NULL,
                    severity ENUM('Important', 'Advisory', 'Optional') NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_rules_culture FOREIGN KEY (culture_id) REFERENCES cultures(id) ON DELETE CASCADE,
                    CONSTRAINT fk_rules_scenario FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
                ) ENGINE=InnoDB
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS saved_advice (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    culture_id INT NOT NULL,
                    scenario_id INT NOT NULL,
                    culture_name VARCHAR(120) NOT NULL,
                    scenario_name VARCHAR(120) NOT NULL,
                    risk_label VARCHAR(20) NOT NULL,
                    risk_percent INT NOT NULL,
                    generated_at VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_saved_advice_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    rating INT NOT NULL,
                    comment VARCHAR(1000) NOT NULL DEFAULT '',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_feedback_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT chk_feedback_rating CHECK (rating BETWEEN 1 AND 5)
                ) ENGINE=InnoDB
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS favorites (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    culture_id INT NOT NULL,
                    scenario_id INT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_favorite (user_id, culture_id, scenario_id),
                    CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT fk_favorites_culture FOREIGN KEY (culture_id) REFERENCES cultures(id) ON DELETE CASCADE,
                    CONSTRAINT fk_favorites_scenario FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
                ) ENGINE=InnoDB
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    culture_id INT NULL,
                    scenario_id INT NULL,
                    detail VARCHAR(500) NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_activity_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    CONSTRAINT fk_activity_culture FOREIGN KEY (culture_id) REFERENCES cultures(id) ON DELETE SET NULL,
                    CONSTRAINT fk_activity_scenario FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE SET NULL
                ) ENGINE=InnoDB
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS community_tips (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    culture_id INT NOT NULL,
                    scenario_id INT NULL,
                    title VARCHAR(160) NOT NULL,
                    tip_text VARCHAR(1000) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_community_tip_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT fk_community_tip_culture FOREIGN KEY (culture_id) REFERENCES cultures(id) ON DELETE CASCADE,
                    CONSTRAINT fk_community_tip_scenario FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE SET NULL
                ) ENGINE=InnoDB
                """
            )

        admin = fetch_one_dict(connection, "SELECT id FROM users WHERE email = %s", ("admin@ceas.local",))
        if not admin:
            execute(
                connection,
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                ("Admin", "admin@ceas.local", hash_password("admin123"), "admin"),
            )

        seed_reference_data(connection)
        refresh_seeded_content(connection)


@app.exception_handler(IntegrityError)
def handle_integrity_error(_: Any, exc: IntegrityError) -> JSONResponse:
    message = str(exc).lower()
    if "duplicate entry" in message:
        detail = "A record with that unique value already exists."
        status_code = status.HTTP_409_CONFLICT
    elif "foreign key constraint fails" in message:
        detail = "Referenced data was not found."
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        detail = "Database constraint failed."
        status_code = status.HTTP_400_BAD_REQUEST
    return JSONResponse(status_code=status_code, content={"detail": detail})


def build_user(row: dict[str, Any]) -> UserOut:
    return UserOut(id=row["id"], name=row["name"], email=row["email"], role=row["role"])


def create_session(connection, user_id: int) -> str:
    token = secrets.token_hex(32)
    execute(connection, "INSERT INTO sessions (token, user_id) VALUES (%s, %s)", (token, user_id))
    return token


def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    token = authorization.split(" ", 1)[1]
    with get_db() as connection:
        user = fetch_one_dict(
            connection,
            """
            SELECT users.id, users.name, users.email, users.role
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = %s
            """,
            (token,),
        )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session.")
    return user


def get_current_user_optional(authorization: str | None = Header(default=None)) -> dict[str, Any] | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    with get_db() as connection:
        return fetch_one_dict(
            connection,
            """
            SELECT users.id, users.name, users.email, users.role
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = %s
            """,
            (token,),
        )


def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


def rule_with_names(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "culture_id": row["culture_id"],
        "scenario_id": row["scenario_id"],
        "culture_name": row["culture_name"],
        "scenario_name": row["scenario_name"],
        "do_text": row["do_text"],
        "dont_text": row["dont_text"],
        "reason": row["reason"],
        "safe_alternative": row["safe_alternative"],
        "severity": row["severity"],
    }


def tokenize(value: str) -> set[str]:
    return {token.strip(".,!?;:()[]{}\"'").lower() for token in value.split() if len(token.strip(".,!?;:()[]{}\"'")) > 2}


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def find_entity_match(name: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    lowered = name.lower()
    for row in rows:
        candidate = row["name"].lower()
        if lowered == candidate or lowered in candidate or candidate in lowered:
            return row
    return None


def context_adjustments(payload: AdviceRequest | SimulationRequest, scenario_name: str) -> dict[str, Any]:
    adjustments: list[str] = []
    safe_actions: list[str] = []
    risk_delta = 0

    if payload.formality == "formal":
        adjustments.append("Keep greetings, posture, and wording more respectful than casual.")
        safe_actions.append("Use titles, polite phrases, and measured body language.")
        risk_delta += 10
    else:
        adjustments.append("Warmth is welcome, but avoid becoming too casual too quickly.")
        safe_actions.append("Match the other person's tone before using humor or first names.")

    if payload.setting == "business":
        adjustments.append("Professional settings raise expectations around punctuality, restraint, and clarity.")
        safe_actions.append("Choose concise, professional language and avoid improvising on sensitive topics.")
        risk_delta += 8
    else:
        adjustments.append("Casual settings allow more flexibility, but host cues still matter.")
        safe_actions.append("Stay observant and friendly without assuming every norm is relaxed.")

    if payload.relationship in {"boss", "client", "elder", "host"}:
        adjustments.append(f"Because the other person is your {payload.relationship}, hierarchy and deference matter more.")
        safe_actions.append("Let the senior or host figure set the rhythm of the interaction.")
        risk_delta += 12
    elif payload.relationship == "friend":
        adjustments.append("Friendlier dynamics may soften formality, but local etiquette still applies.")
        safe_actions.append("Use familiar warmth only after the other person signals comfort.")
        risk_delta -= 4
    else:
        adjustments.append("With limited relationship context, start conservatively and adapt gradually.")
        safe_actions.append("Begin neutral, then mirror the level of familiarity you observe.")
        risk_delta += 4

    if scenario_name == "Business Meeting" and payload.setting == "casual":
        adjustments.append("Even in relaxed meetings, preparation and punctuality still read as respect.")
        risk_delta += 6
    if scenario_name == "Dining" and payload.relationship in {"host", "elder"}:
        adjustments.append("At the table, host and elder cues should guide when to sit, begin, and speak.")
        risk_delta += 6

    return {"adjustments": adjustments, "safe_actions": safe_actions, "risk_delta": risk_delta}


def personal_habit_conflicts(notes: str, rules: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not notes.strip():
        return []
    note_tokens = tokenize(notes)
    conflicts: list[dict[str, str]] = []
    for rule in rules:
        overlap = note_tokens & tokenize(rule["dont_text"])
        if overlap:
            conflicts.append(
                {
                    "habit": notes.strip(),
                    "conflict_with": rule["dont_text"],
                    "warning": f"Your note overlaps with a local 'don't' around {', '.join(sorted(overlap))}.",
                }
            )
    return conflicts[:3]


def advice_from_rows(
    culture: dict[str, Any],
    scenario: dict[str, Any],
    rows: list[dict[str, Any]],
    payload: AdviceRequest,
    user: dict[str, Any] | None,
    connection,
) -> dict[str, Any]:
    severity_weights = {"Important": 3, "Advisory": 2, "Optional": 1}
    base_score = sum(severity_weights[row["severity"]] for row in rows)
    max_score = len(rows) * severity_weights["Important"]
    base_percent = round((base_score / max_score) * 100)
    context = context_adjustments(payload, scenario["name"])

    history_bonus = 0
    if user:
        prior_searches = fetch_one_dict(
            connection,
            """
            SELECT COUNT(*) AS count
            FROM activity_logs
            WHERE user_id = %s AND culture_id = %s AND scenario_id = %s AND event_type = 'advice_search'
            """,
            (user["id"], culture["id"], scenario["id"]),
        )
        history_bonus = min(10, int(prior_searches["count"]) * 2)

    risk_percent = clamp(base_percent + context["risk_delta"] - history_bonus, 10, 98)
    risk_label = "High" if risk_percent >= 70 else "Medium" if risk_percent >= 40 else "Low"
    conflicts = personal_habit_conflicts(payload.user_notes, rows)

    explanation = (
        f"This advice is adjusted for a {payload.formality}, {payload.setting} interaction with a "
        f"{payload.relationship}. The risk is {risk_label.lower()} because etiquette in {scenario['name']} "
        f"depends on both local rules and how sensitive the relationship is."
    )

    return {
        "culture": culture,
        "scenario": scenario,
        "rules": [rule_with_names(row) for row in rows],
        "risk_percent": risk_percent,
        "risk_label": risk_label,
        "context": {
            "formality": payload.formality,
            "setting": payload.setting,
            "relationship": payload.relationship,
            "notes": payload.user_notes,
            "adjustments": context["adjustments"],
        },
        "safe_actions": context["safe_actions"],
        "conflicts": conflicts,
        "explanation": explanation,
        "personalization": {
            "repeat_user_bonus": history_bonus,
            "based_on": "saved history and past searches" if user else "general etiquette model",
        },
    }


def build_simulation_feedback(choice: str, rule: dict[str, Any], payload: SimulationRequest) -> dict[str, Any]:
    choice_tokens = tokenize(choice)
    dont_overlap = len(choice_tokens & tokenize(rule["dont_text"]))
    do_overlap = len(choice_tokens & tokenize(rule["do_text"]))
    severity_weights = {"Important": 3, "Advisory": 2, "Optional": 1}
    score = 55 + do_overlap * 12 - dont_overlap * 18 - severity_weights[rule["severity"]] * 3
    score -= context_adjustments(payload, "Simulation")["risk_delta"] // 3
    score = clamp(score, 5, 95)
    verdict = "Strong choice" if score >= 75 else "Caution" if score >= 45 else "Risky choice"
    return {
        "score": score,
        "verdict": verdict,
        "explanation": rule["reason"],
        "recommended_action": rule["safe_alternative"],
        "matched_do": rule["do_text"],
        "matched_dont": rule["dont_text"],
    }


@app.on_event("startup")
def startup_event() -> None:
    init_db()


def frontend_index_response() -> FileResponse:
    if not FRONTEND_DIST.joinpath("index.html").exists():
        raise HTTPException(status_code=503, detail="Frontend build not found. Run `npm run build` first.")
    return FileResponse(FRONTEND_DIST / "index.html")


@app.get("/")
def serve_index() -> FileResponse:
    return frontend_index_response()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn) -> SessionOut:
    with get_db() as connection:
        existing = fetch_one_dict(connection, "SELECT id FROM users WHERE email = %s", (payload.email.lower(),))
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered.")
        user_id = execute(
            connection,
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (payload.name.strip(), payload.email.lower(), hash_password(payload.password), "user"),
        )
        token = create_session(connection, user_id)
        user = fetch_one_dict(connection, "SELECT id, name, email, role FROM users WHERE id = %s", (user_id,))
    return SessionOut(token=token, user=build_user(user))


@app.post("/api/auth/login", response_model=SessionOut)
def login(payload: LoginIn) -> SessionOut:
    with get_db() as connection:
        user = fetch_one_dict(
            connection,
            "SELECT id, name, email, role FROM users WHERE email = %s AND password_hash = %s",
            (payload.email.lower(), hash_password(payload.password)),
        )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        token = create_session(connection, user["id"])
    return SessionOut(token=token, user=build_user(user))


@app.post("/api/auth/logout")
def logout(user: dict[str, Any] = Depends(get_current_user), authorization: str | None = Header(default=None)) -> dict[str, bool]:
    token = authorization.split(" ", 1)[1]
    with get_db() as connection:
        execute(connection, "DELETE FROM sessions WHERE token = %s AND user_id = %s", (token, user["id"]))
    return {"success": True}


@app.get("/api/auth/me", response_model=UserOut)
def me(user: dict[str, Any] = Depends(get_current_user)) -> UserOut:
    return build_user(user)


@app.get("/api/stats")
def stats() -> dict[str, int]:
    with get_db() as connection:
        cultures = fetch_one_dict(connection, "SELECT COUNT(*) AS count FROM cultures")
        scenarios = fetch_one_dict(connection, "SELECT COUNT(*) AS count FROM scenarios")
        rules = fetch_one_dict(connection, "SELECT COUNT(*) AS count FROM rules")
        users = fetch_one_dict(connection, "SELECT COUNT(*) AS count FROM users")
        feedback = fetch_one_dict(connection, "SELECT COUNT(*) AS count FROM feedback")
    return {
        "cultures": cultures["count"],
        "scenarios": scenarios["count"],
        "rules": rules["count"],
        "users": users["count"],
        "feedback": feedback["count"],
    }


@app.get("/api/users")
def list_users(_: dict[str, Any] = Depends(require_admin)) -> list[dict[str, Any]]:
    with get_db() as connection:
        return fetch_all_dicts(
            connection,
            """
            SELECT users.id, users.name, users.email, users.role, users.created_at,
                   COUNT(DISTINCT saved_advice.id) AS saved_advice_count,
                   COUNT(DISTINCT feedback.id) AS feedback_count
            FROM users
            LEFT JOIN saved_advice ON saved_advice.user_id = users.id
            LEFT JOIN feedback ON feedback.user_id = users.id
            GROUP BY users.id, users.name, users.email, users.role, users.created_at
            ORDER BY users.created_at DESC
            """,
        )


@app.get("/api/favorites")
def list_favorites(user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    with get_db() as connection:
        return fetch_all_dicts(
            connection,
            """
            SELECT favorites.id, favorites.user_id, favorites.culture_id, favorites.scenario_id,
                   cultures.name AS culture_name, scenarios.name AS scenario_name, favorites.created_at
            FROM favorites
            JOIN cultures ON cultures.id = favorites.culture_id
            JOIN scenarios ON scenarios.id = favorites.scenario_id
            WHERE favorites.user_id = %s
            ORDER BY favorites.created_at DESC
            """,
            (user["id"],),
        )


@app.post("/api/favorites", status_code=status.HTTP_201_CREATED)
def create_favorite(payload: FavoriteIn, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with get_db() as connection:
        favorite_id = execute(
            connection,
            "INSERT INTO favorites (user_id, culture_id, scenario_id) VALUES (%s, %s, %s)",
            (user["id"], payload.culture_id, payload.scenario_id),
        )
        return fetch_one_dict(
            connection,
            """
            SELECT favorites.id, favorites.user_id, favorites.culture_id, favorites.scenario_id,
                   cultures.name AS culture_name, scenarios.name AS scenario_name, favorites.created_at
            FROM favorites
            JOIN cultures ON cultures.id = favorites.culture_id
            JOIN scenarios ON scenarios.id = favorites.scenario_id
            WHERE favorites.id = %s
            """,
            (favorite_id,),
        )


@app.delete("/api/favorites/{favorite_id}")
def delete_favorite(favorite_id: int, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, bool]:
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM favorites WHERE id = %s AND user_id = %s", (favorite_id, user["id"]))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Favorite not found.")
    return {"success": True}


@app.get("/api/cultures")
def list_cultures() -> list[dict[str, Any]]:
    with get_db() as connection:
        return fetch_all_dicts(connection, "SELECT id, name, summary, created_at FROM cultures ORDER BY name")


@app.post("/api/cultures", status_code=status.HTTP_201_CREATED)
def create_culture(payload: CultureIn, _: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    with get_db() as connection:
        culture_id = execute(
            connection,
            "INSERT INTO cultures (name, summary) VALUES (%s, %s)",
            (payload.name.strip(), payload.summary.strip()),
        )
        return fetch_one_dict(connection, "SELECT id, name, summary, created_at FROM cultures WHERE id = %s", (culture_id,))


@app.put("/api/cultures/{culture_id}")
def update_culture(culture_id: int, payload: CultureIn, _: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE cultures SET name = %s, summary = %s WHERE id = %s",
                (payload.name.strip(), payload.summary.strip(), culture_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Culture not found.")
        return fetch_one_dict(connection, "SELECT id, name, summary, created_at FROM cultures WHERE id = %s", (culture_id,))


@app.delete("/api/cultures/{culture_id}")
def delete_culture(culture_id: int, _: dict[str, Any] = Depends(require_admin)) -> dict[str, bool]:
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM cultures WHERE id = %s", (culture_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Culture not found.")
    return {"success": True}


@app.get("/api/scenarios")
def list_scenarios() -> list[dict[str, Any]]:
    with get_db() as connection:
        return fetch_all_dicts(connection, "SELECT id, name, description, created_at FROM scenarios ORDER BY name")


@app.post("/api/scenarios", status_code=status.HTTP_201_CREATED)
def create_scenario(payload: ScenarioIn, _: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    with get_db() as connection:
        scenario_id = execute(
            connection,
            "INSERT INTO scenarios (name, description) VALUES (%s, %s)",
            (payload.name.strip(), payload.description.strip()),
        )
        return fetch_one_dict(connection, "SELECT id, name, description, created_at FROM scenarios WHERE id = %s", (scenario_id,))


@app.put("/api/scenarios/{scenario_id}")
def update_scenario(scenario_id: int, payload: ScenarioIn, _: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE scenarios SET name = %s, description = %s WHERE id = %s",
                (payload.name.strip(), payload.description.strip(), scenario_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Scenario not found.")
        return fetch_one_dict(connection, "SELECT id, name, description, created_at FROM scenarios WHERE id = %s", (scenario_id,))


@app.delete("/api/scenarios/{scenario_id}")
def delete_scenario(scenario_id: int, _: dict[str, Any] = Depends(require_admin)) -> dict[str, bool]:
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM scenarios WHERE id = %s", (scenario_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Scenario not found.")
    return {"success": True}


@app.get("/api/rules")
def list_rules(culture_id: int | None = None, scenario_id: int | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT rules.id, rules.culture_id, rules.scenario_id, cultures.name AS culture_name,
               scenarios.name AS scenario_name, rules.do_text, rules.dont_text, rules.reason,
               rules.safe_alternative, rules.severity
        FROM rules
        JOIN cultures ON cultures.id = rules.culture_id
        JOIN scenarios ON scenarios.id = rules.scenario_id
    """
    params: list[Any] = []
    clauses: list[str] = []
    if culture_id:
        clauses.append("rules.culture_id = %s")
        params.append(culture_id)
    if scenario_id:
        clauses.append("rules.scenario_id = %s")
        params.append(scenario_id)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY cultures.name, scenarios.name, rules.id"
    with get_db() as connection:
        return [rule_with_names(row) for row in fetch_all_dicts(connection, query, tuple(params))]


@app.post("/api/rules", status_code=status.HTTP_201_CREATED)
def create_rule(payload: RuleIn, _: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    with get_db() as connection:
        rule_id = execute(
            connection,
            """
            INSERT INTO rules (culture_id, scenario_id, do_text, dont_text, reason, safe_alternative, severity)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payload.culture_id,
                payload.scenario_id,
                payload.do_text.strip(),
                payload.dont_text.strip(),
                payload.reason.strip(),
                payload.safe_alternative.strip(),
                payload.severity,
            ),
        )
        row = fetch_one_dict(
            connection,
            """
            SELECT rules.id, rules.culture_id, rules.scenario_id, cultures.name AS culture_name,
                   scenarios.name AS scenario_name, rules.do_text, rules.dont_text, rules.reason,
                   rules.safe_alternative, rules.severity
            FROM rules
            JOIN cultures ON cultures.id = rules.culture_id
            JOIN scenarios ON scenarios.id = rules.scenario_id
            WHERE rules.id = %s
            """,
            (rule_id,),
        )
    return rule_with_names(row)


@app.put("/api/rules/{rule_id}")
def update_rule(rule_id: int, payload: RuleIn, _: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE rules
                SET culture_id = %s, scenario_id = %s, do_text = %s, dont_text = %s, reason = %s, safe_alternative = %s, severity = %s
                WHERE id = %s
                """,
                (
                    payload.culture_id,
                    payload.scenario_id,
                    payload.do_text.strip(),
                    payload.dont_text.strip(),
                    payload.reason.strip(),
                    payload.safe_alternative.strip(),
                    payload.severity,
                    rule_id,
                ),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Rule not found.")
        row = fetch_one_dict(
            connection,
            """
            SELECT rules.id, rules.culture_id, rules.scenario_id, cultures.name AS culture_name,
                   scenarios.name AS scenario_name, rules.do_text, rules.dont_text, rules.reason,
                   rules.safe_alternative, rules.severity
            FROM rules
            JOIN cultures ON cultures.id = rules.culture_id
            JOIN scenarios ON scenarios.id = rules.scenario_id
            WHERE rules.id = %s
            """,
            (rule_id,),
        )
    return rule_with_names(row)


@app.delete("/api/rules/{rule_id}")
def delete_rule(rule_id: int, _: dict[str, Any] = Depends(require_admin)) -> dict[str, bool]:
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM rules WHERE id = %s", (rule_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Rule not found.")
    return {"success": True}


@app.post("/api/advice/generate")
def generate_advice(payload: AdviceRequest, user: dict[str, Any] | None = Depends(get_current_user_optional)) -> dict[str, Any]:
    with get_db() as connection:
        culture = fetch_one_dict(connection, "SELECT id, name, summary FROM cultures WHERE id = %s", (payload.culture_id,))
        scenario = fetch_one_dict(connection, "SELECT id, name, description FROM scenarios WHERE id = %s", (payload.scenario_id,))
        if not culture or not scenario:
            raise HTTPException(status_code=404, detail="Culture or scenario not found.")
        rows = fetch_all_dicts(
            connection,
            """
            SELECT rules.id, rules.culture_id, rules.scenario_id, cultures.name AS culture_name,
                   scenarios.name AS scenario_name, rules.do_text, rules.dont_text, rules.reason,
                   rules.safe_alternative, rules.severity
            FROM rules
            JOIN cultures ON cultures.id = rules.culture_id
            JOIN scenarios ON scenarios.id = rules.scenario_id
            WHERE rules.culture_id = %s AND rules.scenario_id = %s
            ORDER BY rules.id
            """,
            (payload.culture_id, payload.scenario_id),
        )
        log_activity(
            connection,
            "advice_search",
            user_id=user["id"] if user else None,
            culture_id=payload.culture_id,
            scenario_id=payload.scenario_id,
            detail=f"{culture['name']} | {scenario['name']} | {payload.formality} | {payload.setting} | {payload.relationship}",
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Rules not available.")
        return advice_from_rows(culture, scenario, rows, payload, user, connection)


@app.post("/api/advice/parse")
def parse_nlp_advice(payload: NlpAdviceRequest) -> dict[str, Any]:
    with get_db() as connection:
        cultures = fetch_all_dicts(connection, "SELECT id, name, summary FROM cultures ORDER BY name")
        scenarios = fetch_all_dicts(connection, "SELECT id, name, description FROM scenarios ORDER BY name")

    query = payload.query.lower()
    culture = find_entity_match(query, cultures)
    scenario = find_entity_match(query, scenarios)

    formality = "informal" if any(token in query for token in ("casual", "informal", "friendly", "relaxed")) else "formal"
    setting = "casual" if any(token in query for token in ("casual", "party", "friend", "social", "family")) else "business"
    relationship = "boss"
    for candidate in ("friend", "client", "boss", "host", "colleague", "elder", "stranger"):
        if candidate in query:
            relationship = candidate
            break

    return {
        "query": payload.query,
        "culture": culture,
        "scenario": scenario,
        "context": {
            "formality": formality,
            "setting": setting,
            "relationship": relationship,
        },
        "ready": bool(culture and scenario),
        "message": "Detected a country and scenario from your text." if culture and scenario else "Part of the request was understood. Please confirm any missing fields.",
    }


@app.get("/api/quick-guide/{culture_id}")
def quick_guide(culture_id: int) -> dict[str, Any]:
    with get_db() as connection:
        culture = fetch_one_dict(connection, "SELECT id, name, summary FROM cultures WHERE id = %s", (culture_id,))
        if not culture:
            raise HTTPException(status_code=404, detail="Culture not found.")
        rules = fetch_all_dicts(
            connection,
            """
            SELECT scenarios.name AS scenario_name, rules.do_text, rules.dont_text, rules.severity
            FROM rules
            JOIN scenarios ON scenarios.id = rules.scenario_id
            WHERE rules.culture_id = %s
            ORDER BY FIELD(rules.severity, 'Important', 'Advisory', 'Optional'), rules.id
            LIMIT 5
            """,
            (culture_id,),
        )
    return {
        "culture": culture,
        "dos": [{"scenario": row["scenario_name"], "text": row["do_text"], "severity": row["severity"]} for row in rules[:5]],
        "donts": [{"scenario": row["scenario_name"], "text": row["dont_text"], "severity": row["severity"]} for row in rules[:5]],
    }


@app.post("/api/compare")
def compare_cultures(payload: CompareRequest) -> dict[str, Any]:
    with get_db() as connection:
        left = fetch_one_dict(connection, "SELECT id, name, summary FROM cultures WHERE id = %s", (payload.left_culture_id,))
        right = fetch_one_dict(connection, "SELECT id, name, summary FROM cultures WHERE id = %s", (payload.right_culture_id,))
        scenario = fetch_one_dict(connection, "SELECT id, name, description FROM scenarios WHERE id = %s", (payload.scenario_id,))
        if not left or not right or not scenario:
            raise HTTPException(status_code=404, detail="Comparison input not found.")
        left_rules = fetch_all_dicts(
            connection,
            "SELECT do_text, dont_text, reason, safe_alternative, severity FROM rules WHERE culture_id = %s AND scenario_id = %s ORDER BY id LIMIT 3",
            (payload.left_culture_id, payload.scenario_id),
        )
        right_rules = fetch_all_dicts(
            connection,
            "SELECT do_text, dont_text, reason, safe_alternative, severity FROM rules WHERE culture_id = %s AND scenario_id = %s ORDER BY id LIMIT 3",
            (payload.right_culture_id, payload.scenario_id),
        )
    return {"left": left, "right": right, "scenario": scenario, "left_rules": left_rules, "right_rules": right_rules}


@app.post("/api/mistake-alert")
def mistake_alert(payload: MistakeAlertRequest, user: dict[str, Any] | None = Depends(get_current_user_optional)) -> dict[str, Any]:
    with get_db() as connection:
        culture = fetch_one_dict(connection, "SELECT id, name FROM cultures WHERE id = %s", (payload.culture_id,))
        if not culture:
            raise HTTPException(status_code=404, detail="Culture not found.")
        params: list[Any] = [payload.culture_id]
        query = """
            SELECT scenarios.name AS scenario_name, rules.do_text, rules.dont_text, rules.reason, rules.safe_alternative, rules.severity
            FROM rules
            JOIN scenarios ON scenarios.id = rules.scenario_id
            WHERE rules.culture_id = %s
        """
        if payload.scenario_id:
            query += " AND rules.scenario_id = %s"
            params.append(payload.scenario_id)
        rules = fetch_all_dicts(connection, query, tuple(params))

        action_tokens = tokenize(payload.action_text)
        best_match = None
        best_score = -1
        for rule in rules:
            dont_score = len(action_tokens & tokenize(rule["dont_text"])) * 3
            do_score = len(action_tokens & tokenize(rule["do_text"])) * 2
            reason_score = len(action_tokens & tokenize(rule["reason"]))
            total = dont_score + do_score + reason_score
            if total > best_score:
                best_score = total
                best_match = rule

        severity_weights = {"Important": 3, "Advisory": 2, "Optional": 1}
        if best_match and best_score > 0:
            risk_percent = min(95, 20 + severity_weights[best_match["severity"]] * 20 + best_score * 5)
            risk_label = "High" if risk_percent >= 70 else "Medium" if risk_percent >= 40 else "Low"
            explanation = best_match["reason"]
            safer_alternative = best_match["safe_alternative"]
            scenario_name = best_match["scenario_name"]
            matched_rule = best_match["dont_text"]
        else:
            risk_percent = 25
            risk_label = "Low"
            explanation = f"No direct high-risk etiquette conflict was found for '{payload.action_text}' in {culture['name']}, but context still matters."
            safer_alternative = "Use a polite, neutral response and observe local cues before acting."
            scenario_name = "General"
            matched_rule = "No direct conflict found"

        log_activity(
            connection,
            "mistake_alert",
            user_id=user["id"] if user else None,
            culture_id=payload.culture_id,
            scenario_id=payload.scenario_id,
            detail=payload.action_text[:500],
        )

    return {
        "culture": culture["name"],
        "scenario": scenario_name,
        "action_text": payload.action_text,
        "risk_percent": risk_percent,
        "risk_label": risk_label,
        "matched_rule": matched_rule,
        "explanation": explanation,
        "safer_alternative": safer_alternative,
    }


@app.post("/api/simulation")
def run_simulation(payload: SimulationRequest, user: dict[str, Any] | None = Depends(get_current_user_optional)) -> dict[str, Any]:
    with get_db() as connection:
        culture = fetch_one_dict(connection, "SELECT id, name, summary FROM cultures WHERE id = %s", (payload.culture_id,))
        scenario = fetch_one_dict(connection, "SELECT id, name, description FROM scenarios WHERE id = %s", (payload.scenario_id,))
        if not culture or not scenario:
            raise HTTPException(status_code=404, detail="Culture or scenario not found.")

        rules = fetch_all_dicts(
            connection,
            """
            SELECT rules.id, rules.do_text, rules.dont_text, rules.reason, rules.safe_alternative, rules.severity
            FROM rules
            WHERE rules.culture_id = %s AND rules.scenario_id = %s
            ORDER BY rules.id
            LIMIT 3
            """,
            (payload.culture_id, payload.scenario_id),
        )
        if not rules:
            raise HTTPException(status_code=404, detail="Simulation rules are not available.")

        selected_rule = rules[min(payload.step - 1, len(rules) - 1)]
        feedback = build_simulation_feedback(payload.choice, selected_rule, payload)
        log_activity(
            connection,
            "simulation",
            user_id=user["id"] if user else None,
            culture_id=payload.culture_id,
            scenario_id=payload.scenario_id,
            detail=f"step {payload.step}: {payload.choice[:120]}",
        )

    prompts = {
        1: f"You are entering a {scenario['name'].lower()} situation in {culture['name']}. How do you begin?",
        2: "The other person responds politely. What do you do next?",
        3: "A sensitive moment appears. How do you recover respectfully?",
    }
    return {
        "culture": culture,
        "scenario": scenario,
        "step": payload.step,
        "prompt": prompts.get(payload.step, prompts[3]),
        "feedback": feedback,
        "next_step": payload.step + 1 if payload.step < 3 else None,
        "completed": payload.step >= 3,
    }


@app.get("/api/analytics")
def analytics(_: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    with get_db() as connection:
        most_searched = fetch_all_dicts(
            connection,
            """
            SELECT cultures.name AS culture_name, COUNT(*) AS search_count
            FROM activity_logs
            JOIN cultures ON cultures.id = activity_logs.culture_id
            WHERE activity_logs.event_type = 'advice_search'
            GROUP BY cultures.name
            ORDER BY search_count DESC
            LIMIT 5
            """,
        )
        common_mistakes = fetch_all_dicts(
            connection,
            """
            SELECT detail AS action_text, COUNT(*) AS attempts
            FROM activity_logs
            WHERE event_type = 'mistake_alert' AND detail IS NOT NULL AND detail <> ''
            GROUP BY detail
            ORDER BY attempts DESC
            LIMIT 5
            """,
        )
        feedback_trends = fetch_all_dicts(
            connection,
            """
            SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, ROUND(AVG(rating), 2) AS average_rating, COUNT(*) AS entries
            FROM feedback
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month DESC
            LIMIT 6
            """,
        )
    return {
        "most_searched_countries": most_searched,
        "common_mistakes": common_mistakes,
        "feedback_trends": list(reversed(feedback_trends)),
    }


@app.get("/api/recommendations")
def recommendations(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with get_db() as connection:
        favorite_cultures = fetch_all_dicts(
            connection,
            """
            SELECT cultures.id, cultures.name, COUNT(*) AS weight
            FROM favorites
            JOIN cultures ON cultures.id = favorites.culture_id
            WHERE favorites.user_id = %s
            GROUP BY cultures.id, cultures.name
            ORDER BY weight DESC
            LIMIT 3
            """,
            (user["id"],),
        )
        searched_cultures = fetch_all_dicts(
            connection,
            """
            SELECT cultures.id, cultures.name, COUNT(*) AS weight
            FROM activity_logs
            JOIN cultures ON cultures.id = activity_logs.culture_id
            WHERE activity_logs.user_id = %s AND activity_logs.event_type = 'advice_search'
            GROUP BY cultures.id, cultures.name
            ORDER BY weight DESC
            LIMIT 5
            """,
            (user["id"],),
        )
        scenarios = fetch_all_dicts(
            connection,
            """
            SELECT scenarios.id, scenarios.name, COUNT(*) AS weight
            FROM activity_logs
            JOIN scenarios ON scenarios.id = activity_logs.scenario_id
            WHERE activity_logs.user_id = %s AND activity_logs.event_type = 'advice_search'
            GROUP BY scenarios.id, scenarios.name
            ORDER BY weight DESC
            LIMIT 3
            """,
            (user["id"],),
        )

        ranking: dict[int, dict[str, Any]] = {}
        for source in (favorite_cultures, searched_cultures):
            for item in source:
                current = ranking.setdefault(item["id"], {"culture_id": item["id"], "culture_name": item["name"], "score": 0})
                current["score"] += int(item["weight"])

        ranked = sorted(ranking.values(), key=lambda item: item["score"], reverse=True)[:3]
        top_scenario = scenarios[0]["name"] if scenarios else "Business Meeting"
        recommended = []
        for item in ranked:
            sample_rule = fetch_one_dict(
                connection,
                """
                SELECT scenarios.id AS scenario_id, scenarios.name AS scenario_name, rules.do_text, rules.safe_alternative
                FROM rules
                JOIN scenarios ON scenarios.id = rules.scenario_id
                WHERE rules.culture_id = %s
                ORDER BY CASE WHEN scenarios.name = %s THEN 0 ELSE 1 END, rules.id
                LIMIT 1
                """,
                (item["culture_id"], top_scenario),
            )
            if sample_rule:
                recommended.append({
                    **item,
                    "scenario_id": sample_rule["scenario_id"],
                    "scenario_name": sample_rule["scenario_name"],
                    "do_text": sample_rule["do_text"],
                    "safe_alternative": sample_rule["safe_alternative"],
                })

        if not recommended:
            recommended = fetch_all_dicts(
                connection,
                """
                SELECT cultures.id AS culture_id, cultures.name AS culture_name, scenarios.id AS scenario_id, scenarios.name AS scenario_name,
                       rules.do_text, rules.safe_alternative, 1 AS score
                FROM rules
                JOIN cultures ON cultures.id = rules.culture_id
                JOIN scenarios ON scenarios.id = rules.scenario_id
                ORDER BY FIELD(rules.severity, 'Important', 'Advisory', 'Optional'), cultures.name
                LIMIT 3
                """,
            )

    return {
        "headline": "Recommended for you",
        "based_on": "favorites and recently searched countries",
        "items": recommended,
    }


@app.get("/api/travel-mode/daily-tip")
def daily_travel_tip(user: dict[str, Any] | None = Depends(get_current_user_optional)) -> dict[str, Any]:
    with get_db() as connection:
        base_rule = None
        if user:
            base_rule = fetch_one_dict(
                connection,
                """
                SELECT cultures.name AS culture_name, scenarios.name AS scenario_name, rules.do_text, rules.safe_alternative
                FROM activity_logs
                JOIN rules ON rules.culture_id = activity_logs.culture_id AND rules.scenario_id = activity_logs.scenario_id
                JOIN cultures ON cultures.id = rules.culture_id
                JOIN scenarios ON scenarios.id = rules.scenario_id
                WHERE activity_logs.user_id = %s AND activity_logs.event_type = 'advice_search'
                ORDER BY activity_logs.created_at DESC
                LIMIT 1
                """,
                (user["id"],),
            )
        if not base_rule:
            base_rule = fetch_one_dict(
                connection,
                """
                SELECT cultures.name AS culture_name, scenarios.name AS scenario_name, rules.do_text, rules.safe_alternative
                FROM rules
                JOIN cultures ON cultures.id = rules.culture_id
                JOIN scenarios ON scenarios.id = rules.scenario_id
                ORDER BY FIELD(rules.severity, 'Important', 'Advisory', 'Optional'), rules.id
                LIMIT 1
                """,
            )
    return {
        "title": "Daily etiquette tip",
        "culture_name": base_rule["culture_name"],
        "scenario_name": base_rule["scenario_name"],
        "tip": base_rule["do_text"],
        "backup": base_rule["safe_alternative"],
    }


@app.get("/api/community-tips")
def list_community_tips(culture_id: int | None = None, scenario_id: int | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT community_tips.id, community_tips.user_id, users.name AS user_name, community_tips.culture_id,
               cultures.name AS culture_name, community_tips.scenario_id, scenarios.name AS scenario_name,
               community_tips.title, community_tips.tip_text, community_tips.created_at
        FROM community_tips
        JOIN users ON users.id = community_tips.user_id
        JOIN cultures ON cultures.id = community_tips.culture_id
        LEFT JOIN scenarios ON scenarios.id = community_tips.scenario_id
    """
    params: list[Any] = []
    clauses: list[str] = []
    if culture_id:
        clauses.append("community_tips.culture_id = %s")
        params.append(culture_id)
    if scenario_id:
        clauses.append("community_tips.scenario_id = %s")
        params.append(scenario_id)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY community_tips.created_at DESC LIMIT 30"
    with get_db() as connection:
        return fetch_all_dicts(connection, query, tuple(params))


@app.post("/api/community-tips", status_code=status.HTTP_201_CREATED)
def create_community_tip(payload: CommunityTipIn, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with get_db() as connection:
        tip_id = execute(
            connection,
            """
            INSERT INTO community_tips (user_id, culture_id, scenario_id, title, tip_text)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user["id"], payload.culture_id, payload.scenario_id, payload.title.strip(), payload.tip_text.strip()),
        )
        log_activity(
            connection,
            "community_tip",
            user_id=user["id"],
            culture_id=payload.culture_id,
            scenario_id=payload.scenario_id,
            detail=payload.title.strip(),
        )
        return fetch_one_dict(
            connection,
            """
            SELECT community_tips.id, community_tips.user_id, users.name AS user_name, community_tips.culture_id,
                   cultures.name AS culture_name, community_tips.scenario_id, scenarios.name AS scenario_name,
                   community_tips.title, community_tips.tip_text, community_tips.created_at
            FROM community_tips
            JOIN users ON users.id = community_tips.user_id
            JOIN cultures ON cultures.id = community_tips.culture_id
            LEFT JOIN scenarios ON scenarios.id = community_tips.scenario_id
            WHERE community_tips.id = %s
            """,
            (tip_id,),
        )


@app.delete("/api/community-tips/{tip_id}")
def delete_community_tip(tip_id: int, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, bool]:
    with get_db() as connection:
        with connection.cursor() as cursor:
            if user["role"] == "admin":
                cursor.execute("DELETE FROM community_tips WHERE id = %s", (tip_id,))
            else:
                cursor.execute("DELETE FROM community_tips WHERE id = %s AND user_id = %s", (tip_id, user["id"]))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Community tip not found.")
    return {"success": True}


@app.get("/api/saved-advice")
def list_saved_advice(user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    with get_db() as connection:
        return fetch_all_dicts(
            connection,
            """
            SELECT id, user_id, culture_id, scenario_id, culture_name, scenario_name, risk_label, risk_percent, generated_at, created_at
            FROM saved_advice
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user["id"],),
        )


@app.post("/api/saved-advice", status_code=status.HTTP_201_CREATED)
def create_saved_advice(payload: SaveAdviceIn, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with get_db() as connection:
        saved_id = execute(
            connection,
            """
            INSERT INTO saved_advice (
                user_id, culture_id, scenario_id, culture_name, scenario_name, risk_label, risk_percent, generated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user["id"],
                payload.culture_id,
                payload.scenario_id,
                payload.culture_name,
                payload.scenario_name,
                payload.risk_label,
                payload.risk_percent,
                payload.generated_at,
            ),
        )
        return fetch_one_dict(
            connection,
            """
            SELECT id, user_id, culture_id, scenario_id, culture_name, scenario_name, risk_label, risk_percent, generated_at, created_at
            FROM saved_advice
            WHERE id = %s
            """,
            (saved_id,),
        )


@app.delete("/api/saved-advice/{saved_id}")
def delete_saved_advice(saved_id: int, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, bool]:
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM saved_advice WHERE id = %s AND user_id = %s", (saved_id, user["id"]))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Saved advice not found.")
    return {"success": True}


@app.get("/api/feedback")
def list_feedback(user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    with get_db() as connection:
        if user["role"] == "admin":
            return fetch_all_dicts(
                connection,
                """
                SELECT feedback.id, feedback.user_id, users.name AS user_name, feedback.rating, feedback.comment, feedback.created_at
                FROM feedback
                JOIN users ON users.id = feedback.user_id
                ORDER BY feedback.created_at DESC
                """,
            )
        return fetch_all_dicts(
            connection,
            """
            SELECT feedback.id, feedback.user_id, users.name AS user_name, feedback.rating, feedback.comment, feedback.created_at
            FROM feedback
            JOIN users ON users.id = feedback.user_id
            WHERE feedback.user_id = %s
            ORDER BY feedback.created_at DESC
            """,
            (user["id"],),
        )


@app.post("/api/feedback", status_code=status.HTTP_201_CREATED)
def create_feedback(payload: FeedbackIn, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with get_db() as connection:
        feedback_id = execute(
            connection,
            "INSERT INTO feedback (user_id, rating, comment) VALUES (%s, %s, %s)",
            (user["id"], payload.rating, payload.comment.strip()),
        )
        return fetch_one_dict(
            connection,
            """
            SELECT feedback.id, feedback.user_id, users.name AS user_name, feedback.rating, feedback.comment, feedback.created_at
            FROM feedback
            JOIN users ON users.id = feedback.user_id
            WHERE feedback.id = %s
            """,
            (feedback_id,),
        )


@app.delete("/api/feedback/{feedback_id}")
def delete_feedback(feedback_id: int, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, bool]:
    with get_db() as connection:
        with connection.cursor() as cursor:
            if user["role"] == "admin":
                cursor.execute("DELETE FROM feedback WHERE id = %s", (feedback_id,))
            else:
                cursor.execute("DELETE FROM feedback WHERE id = %s AND user_id = %s", (feedback_id, user["id"]))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Feedback not found.")
    return {"success": True}


app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS, check_dir=False), name="assets")


@app.get("/{full_path:path}")
def serve_frontend_routes(full_path: str) -> FileResponse:
    if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi"):
        raise HTTPException(status_code=404, detail="Not found.")
    return frontend_index_response()
