from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.database import get_db
from app.models import Profile
from app.schemas import ProfileCreate, ProfileResponse, ProfileListItem
from app.services.external_apis import fetch_all
from uuid6 import uuid7
from datetime import datetime, timezone
from typing import Optional
import re

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


# ─── Constants ───────────────────────────────────────────────────────────────

VALID_SORT_FIELDS = {"age", "created_at", "gender_probability"}
VALID_ORDERS = {"asc", "desc"}
VALID_AGE_GROUPS = {"child", "teenager", "adult", "senior"}
VALID_GENDERS = {"male", "female"}

COUNTRY_NAMES = {
    "NG": "Nigeria",
    "GH": "Ghana",
    "KE": "Kenya",
    "ZA": "South Africa",
    "AO": "Angola",
    "ET": "Ethiopia",
    "EG": "Egypt",
    "TZ": "Tanzania",
    "UG": "Uganda",
    "CM": "Cameroon",
    "CI": "Côte d'Ivoire",
    "SN": "Senegal",
    "BJ": "Benin",
    "TG": "Togo",
    "BF": "Burkina Faso",
    "ML": "Mali",
    "NE": "Niger",
    "GN": "Guinea",
    "RW": "Rwanda",
    "MZ": "Mozambique",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
    "MW": "Malawi",
    "LS": "Lesotho",
    "SZ": "Eswatini",
    "NA": "Namibia",
    "BW": "Botswana",
    "MG": "Madagascar",
    "US": "United States",
    "GB": "United Kingdom",
    "FR": "France",
    "DE": "Germany",
    "IT": "Italy",
    "ES": "Spain",
    "PT": "Portugal",
    "NL": "Netherlands",
    "BE": "Belgium",
    "CH": "Switzerland",
    "CA": "Canada",
    "AU": "Australia",
    "NZ": "New Zealand",
    "IN": "India",
    "PK": "Pakistan",
    "BD": "Bangladesh",
    "LK": "Sri Lanka",
    "BR": "Brazil",
    "MX": "Mexico",
    "AR": "Argentina",
    "CO": "Colombia",
    "CN": "China",
    "JP": "Japan",
    "KR": "South Korea",
    "ID": "Indonesia",
    "PH": "Philippines",
    "VN": "Vietnam",
    "TH": "Thailand",
    "MY": "Malaysia",
    "TR": "Turkey",
    "SA": "Saudi Arabia",
    "AE": "United Arab Emirates",
    "IR": "Iran",
    "IQ": "Iraq",
    "MA": "Morocco",
    "DZ": "Algeria",
    "TN": "Tunisia",
    "LY": "Libya",
    "SD": "Sudan",
    "SS": "South Sudan",
    "SO": "Somalia",
    "CD": "DR Congo",
    "CG": "Congo",
    "GA": "Gabon",
    "GQ": "Equatorial Guinea",
    "CF": "Central African Republic",
    "TD": "Chad",
    "ER": "Eritrea",
    "DJ": "Djibouti",
    "KM": "Comoros",
    "MU": "Mauritius",
    "SC": "Seychelles",
    "CV": "Cape Verde",
    "GM": "Gambia",
    "GW": "Guinea-Bissau",
    "SL": "Sierra Leone",
    "LR": "Liberia",
    "MR": "Mauritania",
    "ST": "São Tomé and Príncipe",
    "RU": "Russia",
    "UA": "Ukraine",
    "PL": "Poland",
    "RO": "Romania",
    "CZ": "Czech Republic",
    "HU": "Hungary",
    "SK": "Slovakia",
    "AT": "Austria",
    "SE": "Sweden",
    "NO": "Norway",
    "DK": "Denmark",
    "FI": "Finland",
    "GR": "Greece",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "RS": "Serbia",
    "BA": "Bosnia and Herzegovina",
    "SI": "Slovenia",
    "MK": "North Macedonia",
    "AL": "Albania",
    "ME": "Montenegro",
    "XK": "Kosovo",
    "MD": "Moldova",
    "BY": "Belarus",
    "LT": "Lithuania",
    "LV": "Latvia",
    "EE": "Estonia",
    "IS": "Iceland",
    "IE": "Ireland",
    "LU": "Luxembourg",
    "MT": "Malta",
    "CY": "Cyprus",
    "IL": "Israel",
    "JO": "Jordan",
    "LB": "Lebanon",
    "SY": "Syria",
    "YE": "Yemen",
    "OM": "Oman",
    "KW": "Kuwait",
    "QA": "Qatar",
    "BH": "Bahrain",
    "AF": "Afghanistan",
    "UZ": "Uzbekistan",
    "KZ": "Kazakhstan",
    "TM": "Turkmenistan",
    "TJ": "Tajikistan",
    "KG": "Kyrgyzstan",
    "AZ": "Azerbaijan",
    "AM": "Armenia",
    "GE": "Georgia",
    "MM": "Myanmar",
    "KH": "Cambodia",
    "LA": "Laos",
    "NP": "Nepal",
    "BT": "Bhutan",
    "MV": "Maldives",
    "TW": "Taiwan",
    "HK": "Hong Kong",
    "MN": "Mongolia",
    "PG": "Papua New Guinea",
    "FJ": "Fiji",
    "VE": "Venezuela",
    "PE": "Peru",
    "EC": "Ecuador",
    "BO": "Bolivia",
    "PY": "Paraguay",
    "UY": "Uruguay",
    "CL": "Chile",
    "GY": "Guyana",
    "SR": "Suriname",
    "CU": "Cuba",
    "DO": "Dominican Republic",
    "HT": "Haiti",
    "JM": "Jamaica",
    "TT": "Trinidad and Tobago",
    "BB": "Barbados",
    "LC": "Saint Lucia",
    "VC": "Saint Vincent",
    "GD": "Grenada",
    "AG": "Antigua and Barbuda",
    "DM": "Dominica",
    "KN": "Saint Kitts and Nevis",
    "BS": "Bahamas",
    "BZ": "Belize",
    "GT": "Guatemala",
    "HN": "Honduras",
    "SV": "El Salvador",
    "NI": "Nicaragua",
    "CR": "Costa Rica",
    "PA": "Panama",
}

COUNTRY_NAME_TO_CODE = {v.lower(): k for k, v in COUNTRY_NAMES.items()}
COUNTRY_NAME_TO_CODE.update(
    {
        "nigeria": "NG",
        "ghana": "GH",
        "kenya": "KE",
        "south africa": "ZA",
        "angola": "AO",
        "ethiopia": "ET",
        "egypt": "EG",
        "tanzania": "TZ",
        "uganda": "UG",
        "cameroon": "CM",
        "senegal": "SN",
        "benin": "BJ",
        "togo": "TG",
        "niger": "NE",
        "guinea": "GN",
        "rwanda": "RW",
        "us": "US",
        "uk": "GB",
        "united states": "US",
        "united kingdom": "GB",
        "america": "US",
        "britain": "GB",
        "england": "GB",
        "india": "IN",
        "china": "CN",
        "japan": "JP",
        "brazil": "BR",
        "france": "FR",
        "germany": "DE",
        "italy": "IT",
        "spain": "ES",
        "canada": "CA",
        "australia": "AU",
        "russia": "RU",
    }
)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _apply_filters(
    stmt,
    gender,
    age_group,
    country_id,
    min_age,
    max_age,
    min_gender_probability,
    min_country_probability,
):
    if gender is not None:
        if gender.lower() not in VALID_GENDERS:
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "Invalid query parameters"},
            )
        stmt = stmt.where(func.lower(Profile.gender) == gender.lower())
    if age_group is not None:
        if age_group.lower() not in VALID_AGE_GROUPS:
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "Invalid query parameters"},
            )
        stmt = stmt.where(func.lower(Profile.age_group) == age_group.lower())
    if country_id is not None:
        stmt = stmt.where(func.upper(Profile.country_id) == country_id.upper())
    if min_age is not None:
        stmt = stmt.where(Profile.age >= min_age)
    if max_age is not None:
        stmt = stmt.where(Profile.age <= max_age)
    if min_gender_probability is not None:
        stmt = stmt.where(Profile.gender_probability >= min_gender_probability)
    if min_country_probability is not None:
        stmt = stmt.where(Profile.country_probability >= min_country_probability)
    return stmt


def _apply_sorting(stmt, sort_by, order):
    if sort_by is not None:
        if sort_by not in VALID_SORT_FIELDS:
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "Invalid query parameters"},
            )
        if order not in VALID_ORDERS:
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "Invalid query parameters"},
            )
        col = getattr(Profile, sort_by)
        stmt = stmt.order_by(col.asc() if order == "asc" else col.desc())
    return stmt


def _parse_nl_query(q: str) -> dict:
    text = q.lower().strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": "Unable to interpret query"},
        )

    filters = {}

    # ── Gender ───────────────────────────────────────────────────────────────
    if "male and female" in text or "female and male" in text:
        pass  # both → no gender filter
    elif "female" in text:
        filters["gender"] = "female"
    elif "male" in text:
        filters["gender"] = "male"

    # ── Age group keywords ───────────────────────────────────────────────────
    if "teenager" in text or "teenagers" in text:
        filters["age_group"] = "teenager"
    elif "child" in text or "children" in text:
        filters["age_group"] = "child"
    elif "senior" in text or "seniors" in text or "elderly" in text:
        filters["age_group"] = "senior"
    elif "adult" in text or "adults" in text:
        filters["age_group"] = "adult"
    elif "young" in text:
        filters["min_age"] = 16
        filters["max_age"] = 24

    # ── Explicit age comparisons ─────────────────────────────────────────────
    above_match = re.search(r"above\s+(\d+)", text)
    below_match = re.search(r"below\s+(\d+)", text)
    over_match = re.search(r"over\s+(\d+)", text)
    under_match = re.search(r"under\s+(\d+)", text)
    between_match = re.search(r"between\s+(\d+)\s+and\s+(\d+)", text)

    if between_match:
        filters["min_age"] = int(between_match.group(1))
        filters["max_age"] = int(between_match.group(2))
    else:
        if above_match:
            filters["min_age"] = int(above_match.group(1))
        if over_match:
            filters["min_age"] = int(over_match.group(1))
        if below_match:
            filters["max_age"] = int(below_match.group(1))
        if under_match:
            filters["max_age"] = int(under_match.group(1))

    # ── Country ──────────────────────────────────────────────────────────────
    from_match = re.search(
        r"from\s+([a-z\s]+?)(?:\s+(?:above|below|over|under|between|aged?|who|with|where)|$)",
        text,
    )
    if from_match:
        country_raw = from_match.group(1).strip().rstrip(".,")
        code = COUNTRY_NAME_TO_CODE.get(country_raw)
        if not code:
            for name, iso in COUNTRY_NAME_TO_CODE.items():
                if name in country_raw or country_raw in name:
                    code = iso
                    break
        if code:
            filters["country_id"] = code
    else:
        for name, iso in sorted(COUNTRY_NAME_TO_CODE.items(), key=lambda x: -len(x[0])):
            if name in text:
                filters["country_id"] = iso
                break

    if not filters:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": "Unable to interpret query"},
        )

    return filters


# ─── Routes ──────────────────────────────────────────────────────────────────


@router.post("", status_code=201)
async def create_profile(body: ProfileCreate, db: AsyncSession = Depends(get_db)):
    name = body.name.strip()

    if not name:
        raise HTTPException(
            status_code=400, detail={"status": "error", "message": "Name is required"}
        )

    result = await db.execute(
        select(Profile).where(func.lower(Profile.name) == name.lower())
    )
    existing = result.scalar_one_or_none()

    if existing:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": ProfileResponse.model_validate(existing),
        }

    enriched = await fetch_all(name)

    profile = Profile(
        id=str(uuid7()),
        name=name.lower(),
        created_at=datetime.now(timezone.utc),
        **enriched
    )

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return {"status": "success", "data": ProfileResponse.model_validate(profile)}


# NOTE: /search must be defined BEFORE /{id} so FastAPI doesn't treat
# the literal string "search" as a profile ID.
@router.get("/search")
async def search_profiles(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    filters = _parse_nl_query(q)

    stmt = select(Profile)
    stmt = _apply_filters(
        stmt,
        gender=filters.get("gender"),
        age_group=filters.get("age_group"),
        country_id=filters.get("country_id"),
        min_age=filters.get("min_age"),
        max_age=filters.get("max_age"),
        min_gender_probability=None,
        min_country_probability=None,
    )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    offset = (page - 1) * limit
    results = (await db.execute(stmt.offset(offset).limit(limit))).scalars().all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": [ProfileListItem.model_validate(p) for p in results],
    }


@router.get("")
async def list_profiles(
    # filters
    gender: Optional[str] = Query(None),
    age_group: Optional[str] = Query(None),
    country_id: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None, ge=0),
    max_age: Optional[int] = Query(None, ge=0),
    min_gender_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
    min_country_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
    # sorting
    sort_by: Optional[str] = Query(None),
    order: str = Query("asc"),
    # pagination
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Profile)
    stmt = _apply_filters(
        stmt,
        gender,
        age_group,
        country_id,
        min_age,
        max_age,
        min_gender_probability,
        min_country_probability,
    )
    stmt = _apply_sorting(stmt, sort_by, order)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    offset = (page - 1) * limit
    results = (await db.execute(stmt.offset(offset).limit(limit))).scalars().all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": [ProfileListItem.model_validate(p) for p in results],
    }


@router.get("/{id}")
async def get_profile(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.id == id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=404, detail={"status": "error", "message": "Profile not found"}
        )

    return {"status": "success", "data": ProfileResponse.model_validate(profile)}


@router.delete("/{id}", status_code=204)
async def delete_profile(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.id == id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=404, detail={"status": "error", "message": "Profile not found"}
        )

    await db.delete(profile)
    await db.commit()
    return Response(status_code=204)
