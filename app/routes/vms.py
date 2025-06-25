# app/routes/vms.py
from fastapi import APIRouter
from app.services.vm_info import list_vms
from app.services.metrics import get_cpu_usage

router = APIRouter()

@router.get("/vms")
def get_vms():
    vms = list_vms()
    for vm in vms:
        vm["cpu_usage"] = round(get_cpu_usage(vm["vm_id"]) or 0, 2)
    return {"vms": vms}

@router.get("/vms/underutilized")
def get_low_cpu_vms():
    vms = list_vms()
    result = []
    for vm in vms:
        cpu = get_cpu_usage(vm["vm_id"])
        if cpu and cpu < 20:
            vm["cpu_usage"] = round(cpu, 2)
            result.append(vm)
    return {"underutilized_vms": result}
