# app/routes/metrics.py
from fastapi import APIRouter
from app.services.metrics import get_cpu_usage

router = APIRouter()

@router.get("/metrics/{vm_id}")
def cpu_for_vm(vm_id: str):
    usage = get_cpu_usage(vm_id)
    return {"vm_id": vm_id, "cpu_usage": round(usage, 2) if usage else "N/A"}
