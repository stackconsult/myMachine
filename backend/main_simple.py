from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="CEP Machine Backend", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "CEP Machine Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cep-machine-backend"}

@app.get("/api/layers")
async def get_layers():
    return {
        "layers": [
            {"id": 1, "name": "Prospect Research", "status": "active"},
            {"id": 2, "name": "Pitch Generator", "status": "active"},
            {"id": 3, "name": "Outreach Engine", "status": "active"},
            {"id": 4, "name": "Booking Handler", "status": "active"},
            {"id": 5, "name": "Onboarding Flow", "status": "active"},
            {"id": 6, "name": "GBP Optimizer", "status": "active"},
            {"id": 7, "name": "Reporting Engine", "status": "active"},
            {"id": 8, "name": "Finance Tracker", "status": "active"},
            {"id": 9, "name": "Self-Learning", "status": "active"},
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
