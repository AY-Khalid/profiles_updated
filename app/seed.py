"""
Seed the database with 2026 profiles.
Run:  python -m app.seed
Re-running is safe — duplicates are skipped via ON CONFLICT DO NOTHING.
"""

import asyncio
import json
from sqlalchemy import func
from sqlalchemy.future import select
from app.database import engine, AsyncSessionLocal, Base
from app.models import Profile
from app.services.external_apis import fetch_all
from uuid6 import uuid7
from datetime import datetime, timezone


with open("seed_profiles.json", "r") as f:
    profiles_raw = json.load(f)

print(type(profiles_raw)) 
print(list(profiles_raw.keys()))

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


def compute_age_group(age: int) -> str:
    if age < 13:
        return "child"
    elif age < 18:
        return "teenager"
    elif age < 65:
        return "adult"
    else:
        return "senior"


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    with open("seed_profiles.json", "r") as f:
        data = json.load(f)

    names = data[
        "profiles"
    ]  # it's a dict with a "profiles" key containing a list of strings

    async with AsyncSessionLocal() as db:
        for name in names:
            name = name.strip()

            # skip if already exists
            result = await db.execute(
                select(Profile).where(func.lower(Profile.name) == name.lower())
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"⏭ Skipping (exists): {name}")
                continue

            try:
                enriched = await fetch_all(name)

                profile = Profile(
                    id=str(uuid7()),
                    name=name.lower(),
                    created_at=datetime.now(timezone.utc),
                    **enriched,
                )
                db.add(profile)
                await db.commit()
                print(f"Seeded: {name}")
            except Exception as e:
                await db.rollback()
                print(f"Failed: {name} — {e}")

    print("Seeding complete.")
