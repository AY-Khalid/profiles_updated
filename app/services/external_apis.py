import httpx
import asyncio
from fastapi import HTTPException


def classify_age(age: int) -> str:
    if age <= 12:
        return "child"
    elif age <= 19:
        return "teenager"
    elif age <= 59:
        return "adult"
    else:
        return "senior"


async def fetch_all(name: str) -> dict:
    async with httpx.AsyncClient() as client:
        gender_res, age_res, nation_res = await asyncio.gather(
            client.get(f"https://api.genderize.io?name={name}"),
            client.get(f"https://api.agify.io?name={name}"),
            client.get(f"https://api.nationalize.io?name={name}"),
        )

    gender_data = gender_res.json()
    age_data = age_res.json()
    nation_data = nation_res.json()

    # Validate Genderize
    if not gender_data.get("gender") or gender_data.get("count", 0) == 0:
        raise HTTPException(
            status_code=502,
            detail={
                "status": "502",
                "message": "Genderize returned an invalid response",
            },
        )

    # Validate Agify
    if age_data.get("age") is None:
        raise HTTPException(
            status_code=502,
            detail={"status": "502", "message": "Agify returned an invalid response"},
        )

    # Validate Nationalize
    countries = nation_data.get("country", [])
    if not countries:
        raise HTTPException(
            status_code=502,
            detail={
                "status": "502",
                "message": "Nationalize returned an invalid response",
            },
        )

    age = age_data["age"]
    top_country = max(countries, key=lambda c: c["probability"])

    return {
        "gender": gender_data["gender"],
        "gender_probability": gender_data["probability"],
        "sample_size": gender_data["count"],
        "age": age,
        "age_group": classify_age(age),
        "country_id": top_country["country_id"],
        "country_name": COUNTRY_NAMES.get(top_country["country_id"], top_country["country_id"]),
        "country_probability": top_country["probability"],
    }
