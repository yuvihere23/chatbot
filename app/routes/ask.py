from fastapi import APIRouter
from pydantic import BaseModel
from app.services.vm_info import list_vms
from app.services.metrics import get_cpu_usage
from app.services.gemini import extract_intent, generate_final_answer

router = APIRouter()

class Query(BaseModel):
    prompt: str

@router.post("/ask")
def ask_bot(query: Query):
    prompt = query.prompt
    intent_result = extract_intent(prompt)

    print("=== INTENT ===")
    print(intent_result)

    # 🧠 Parse intent
    if "list_all_vms" in intent_result:
        vms = list_vms()
        for vm in vms:
            vm["cpu_usage"] = round(get_cpu_usage(vm["vm_id"]) or 0, 2)
        final_response = generate_final_answer(prompt, vms)
        return {"answer": final_response, "raw_data": vms}

    elif "underutilized_vms" in intent_result:
        vms = list_vms()
        result = []
        for vm in vms:
            cpu = get_cpu_usage(vm["vm_id"])
            if cpu and cpu < 20:
                vm["cpu_usage"] = round(cpu, 2)
                result.append(vm)
        final_response = generate_final_answer(prompt, result)
        return {"answer": final_response, "raw_data": result}

    return {"error": "Unknown intent", "intent": intent_result}
