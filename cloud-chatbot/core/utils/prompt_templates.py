classification_prompt = """**Cloud Infrastructure Query Classification**
Analyze this query and respond in JSON format only:

{{
  "query_type": "simple" or "complex",
  "intent": "list_vms"|"vm_details"|"list_volumes"|"complex_filter",
  "parameters": {{
    "resource_type": "vm"|"volume"|"vpc"|"subnet",
    "resource_id": "string|none",
    "filters": {{
      "key": "value",
      "numeric_comparisons": {{
        "key": {{"operator": ">|<|=", "value": number}}
      }}
    }}
  }}
}}

**Query to analyze:**
{query}

**Examples:**
1. "show my running ec2 instances":
{{
  "query_type": "simple",
  "intent": "list_vms",
  "parameters": {{
    "resource_type": "vm",
    "filters": {{"state": "running"}}
  }}
}}

2. "vms with cpu over 90%":
{{
  "query_type": "complex",
  "intent": "complex_filter",
  "parameters": {{
    "resource_type": "vm",
    "filters": {{
      "numeric_comparisons": {{
        "cpu": {{"operator": ">", "value": 90}}
      }}
    }}
  }}
}}
"""