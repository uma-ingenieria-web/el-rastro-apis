from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx

import os

app = FastAPI()

CO2_RATE = 0.013

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

versionRoute = "api/v2"

load_dotenv()

API_KEY = os.getenv("X_APIKEY")


@app.get("/" + versionRoute + "/carbon")
async def get_carbon(
    origin_lat: float = Query(..., description="Latitude of the origin"),
    origin_lon: float = Query(..., description="Longitude of the origin"),
    destination_lat: float = Query(..., description="Latitude of the destination"),
    destination_lon: float = Query(..., description="Longitude of the destination"),
    weight: float = Query(..., description="Weight of the load")
):
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.freightos.com/api/v1/co2calc"
            
            if API_KEY is None:
                return {"error": "API_KEY is not set"}

            headers = {"Content-Type": "application/json", "x-apikey": API_KEY}
            response = await client.post(
                url,
                headers=headers,
                json={
                    "load": [
                        {"quantity": 1, "unitWeightKg": weight, "unitType": "boxes"}
                    ],
                    "legs": [
                        {
                            "mode": "LTL",
                            "origin": {
                                "longitude": origin_lat,
                                "latitude": origin_lon,
                            },
                            "destination": {
                                "lonitude": destination_lat,
                                "latitude": destination_lon,
                            },
                            "carrierCode": "MEAU",
                        }
                    ],
                },
            )

            if response.status_code == 200:
                json_content = response.json()
                return CO2_RATE * (json_content.get("Ew") + json_content.get("Et"))
            else:
                return {"error": f"HTTP Error: {response.status_code}"}
    except HTTPException as e:
        return {"error": f"HTTP Exception: {str(e)}"}

