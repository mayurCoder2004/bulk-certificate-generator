from fastapi import FastAPI

app = FastAPI(
    title="Bulk Certificate Generator API",
    description="API for generating certificates in bulk.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
