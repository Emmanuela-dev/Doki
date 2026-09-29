from fastapi import FastAPI

from app.payments.router import router as payments_router


app = FastAPI(title="Doki API")
app.include_router(payments_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}