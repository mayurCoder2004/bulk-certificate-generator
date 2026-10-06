from fastapi import FastAPI

from app.api.routes.jobs import router as jobs_router


app = FastAPI(
    title="Bulk Certificate Generator",
    version="1.0.0",
)


app.include_router(jobs_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
