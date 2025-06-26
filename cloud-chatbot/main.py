# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import logging
# from core.models.query import QueryRequest, QueryType
# from core.models.query import QueryResponse
# from core.services.query_classifier import QueryClassifier
# from core.services.script_generator import ScriptGenerator
# from core.services.script_executor import ScriptExecutor
# from core.adapters.aws_adapter import AWSAdapter
# from core.adapters.azure_adapter import AzureAdapter
# from core.models.resource import VirtualMachine
# from core.services.api_handler import get_adapter, router as api_router
# from core.services.query_classifier import QueryClassifier
# from core.services.gemini_classifier import GeminiClassifier

# app = FastAPI()

# # Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Initialize services
# query_classifier = QueryClassifier(gemini_api_key="your-api-key-here")
# script_generator = ScriptGenerator()
# script_executor = ScriptExecutor()

# # Include API routes
# app.include_router(api_router, prefix="/api/v1")

# @app.post("/query")
# async def handle_query(query: QueryRequest):
#     query_type, intent = query_classifier.classify(query)
    
#     if query_type == QueryType.SIMPLE:
#         if intent == "list_vms":
#             # Handle listing VMs with filters
#             vms = adapter.list_vms(query.filters)
#             return QueryResponse(
#                 success=True,
#                 data=vms,
#                 query_type=query_type
#             )
#         elif intent == "vm_details":
#             # Handle VM details
#             vm_id = query.filters.get("resource_id")
#             if vm_id:
#                 vm = adapter.get_vm_details(vm_id)
#                 return QueryResponse(
#                     success=True,
#                     data=vm,
#                     query_type=query_type
#                 )
        
#         # ... rest of your complex query handling ...
        
#         else:
#             # Handle complex queries
#             script = script_generator.generate_aws_script(query)
#             raw_result = script_executor.execute(script)
            
#             if not raw_result:  # Handle empty case
#                 return QueryResponse(
#                     success=True,
#                     data=[],
#                     query_type=query_type
#                 )
            
#             # Convert to VirtualMachine objects
#             vms = []
#             for item in raw_result:
#                 try:
#                     if 'state' not in item:
#                         item['state'] = 'unknown'
#                     vms.append(VirtualMachine(**item))
#                 except Exception as e:
#                     logging.error(f"Error parsing VM data: {str(e)}")
#                     continue
            
#             return QueryResponse(
#                 success=True,
#                 data=vms,
#                 query_type=query_type
#             )
            
#     except HTTPException as he:
#         return QueryResponse(
#             success=False,
#             error=str(he.detail),
#             query_type=QueryType.COMPLEX
#         )
#     except Exception as e:
#         logging.error(f"Unexpected error: {str(e)}", exc_info=True)
#         return QueryResponse(
#             success=False,
#             error="Internal server error",
#             query_type=QueryType.COMPLEX
#         )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from core.models.query import QueryRequest, QueryType, QueryResponse
from core.services.query_classifier import QueryClassifier
from core.services.script_generator import ScriptGenerator
from core.services.script_executor import ScriptExecutor
from core.adapters.aws_adapter import AWSAdapter
from core.adapters.azure_adapter import AzureAdapter
from core.models.resource import VirtualMachine
from core.services.api_handler import router as api_router
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
query_classifier = QueryClassifier(gemini_api_key=os.getenv("GOOGLE_API_KEY"))
script_generator = ScriptGenerator()
script_executor = ScriptExecutor()

# Include API routes
app.include_router(api_router, prefix="/api/v1")

def get_adapter(cloud: str):
    """Factory function to get the appropriate cloud adapter"""
    try:
        if cloud.lower() == "aws":
            return AWSAdapter()
        elif cloud.lower() == "azure":
            return AzureAdapter()
        raise ValueError(f"Unsupported cloud provider: {cloud}")
    except Exception as e:
        logging.error(f"Adapter initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def handle_query(query: QueryRequest):
    try:
        # Get the appropriate cloud adapter
        adapter = get_adapter(query.cloud)
        
        # Classify the query
        query_type, intent = query_classifier.classify(query)
        
        if query_type == QueryType.SIMPLE:
            if intent == "list_vms":
                # Handle listing VMs with filters
                vms = adapter.list_vms(query.filters)
                return QueryResponse(
                    success=True,
                    data=vms,
                    query_type=query_type
                )
                
            elif intent == "vm_details":
                # Handle VM details
                vm_id = query.filters.get("resource_id")
                if vm_id:
                    vm = adapter.get_vm_details(vm_id)
                    vm.cpu_utilization = adapter.get_vm_utilization(vm_id)
                    vm.volumes = adapter.get_volumes(vm_id)
                    return QueryResponse(
                        success=True,
                        data=vm,
                        query_type=query_type
                    )
                else:
                    return QueryResponse(
                        success=False,
                        error="VM ID not specified",
                        query_type=query_type
                    )
                    
            elif intent == "list_volumes":
                volumes = adapter.get_volumes()
                return QueryResponse(
                    success=True,
                    data=volumes,
                    query_type=query_type
                )
                
            else:
                return QueryResponse(
                    success=False,
                    error=f"Unsupported simple query type: {intent}",
                    query_type=query_type
                )
                
        else:  # Complex queries
            script = script_generator.generate_aws_script(query)
            raw_result = script_executor.execute(script)
            
            if not raw_result:
                return QueryResponse(
                    success=True,
                    data=[],
                    query_type=query_type
                )
            
            # Convert to VirtualMachine objects
            vms = []
            for item in raw_result:
                try:
                    if 'state' not in item:
                        item['state'] = 'unknown'
                    vms.append(VirtualMachine(**item))
                except Exception as e:
                    logging.error(f"Error parsing VM data: {str(e)}")
                    continue
            
            return QueryResponse(
                success=True,
                data=vms,
                query_type=query_type
            )
            
    except HTTPException as he:
        return QueryResponse(
            success=False,
            error=str(he.detail),
            query_type=QueryType.COMPLEX
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        return QueryResponse(
            success=False,
            error="Internal server error",
            query_type=QueryType.COMPLEX
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)