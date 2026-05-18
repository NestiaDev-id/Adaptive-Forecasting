from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from disaster_forecaster import ChronosDisasterForecaster

app = FastAPI(title="Adaptive Forecasting Engine - Disaster AI Lab")

# Configure CORS so Vercel Frontend can hit this space directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the forecaster
forecaster = ChronosDisasterForecaster()

class ForecastRequest(BaseModel):
    limit: int = 50
    horizon: int = 10
    zone: str | None = None

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "model": "Chronos-2 Disaster Predictor", 
        "location": "Hugging Face Space",
        "ready": forecaster.model_loaded
    }

@app.get("/zones")
def list_zones():
    """Returns all available seismic zones with event counts."""
    return forecaster.get_available_zones()

@app.post("/analyze/earthquake")
def analyze_earthquake(req: ForecastRequest):
    """Run Chronos forecast on earthquake magnitude trends, optionally filtered by zone."""
    result = forecaster.forecast_earthquakes(
        limit=req.limit, 
        horizon=req.horizon, 
        zone=req.zone
    )
    return result

if __name__ == "__main__":
    # Hugging Face Spaces expects the app to run on port 7860
    uvicorn.run(app, host="0.0.0.0", port=7860)
