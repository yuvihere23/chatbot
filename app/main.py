from fastapi import FastAPI
from app.routes import ask, vms, metrics, network

app = FastAPI(
    title="Azure GPT Cloud Bot",
    description="Chatbot API to answer Azure infra queries",
    version="0.1.0"
)

app.include_router(ask.router, prefix="/api")
app.include_router(vms.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(network.router, prefix="/api")
