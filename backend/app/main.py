from fastapi import FastAPI

app = FastAPI(title="Code Documentation Assistant")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
