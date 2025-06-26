# import re
# from enum import Enum
# from typing import Tuple
# from core.models.query import QueryRequest, QueryType

# class QueryClassifier:
#     def __init__(self):
#         self.simple_patterns = {
#             "list_vms": [
#                 r"list(?: all| my)? (?:vms|instances|ec2)",
#                 r"show(?: me| all)? (?:running|stopped) instances",
#                 r"get (?:vms|instances) list"
#             ],
#             "vm_details": [
#                 r"details (?:for|about) (?:instance|vm) (\w+)",
#                 r"show (?:me )?(?:info|details) (?:for|about) (\w+)"
#             ],
#             "list_vpcs": [
#                 r"list(?: all)? vpcs",
#                 r"show(?: me)? (?:vpcs|virtual networks)"
#             ],
#             "list_subnets": [
#                 r"list(?: all)? subnets",
#                 r"show(?: me)? subnets(?: for vpc (\w+))?"
#             ]
#         }
        
#         self.complex_indicators = [
#             'with', 'and', 'or', 'utilization', 'cpu', 'memory',
#             'disk', 'storage', 'cost', '>', '<', '>=', '<=', 
#             'between', 'average', 'max', 'min', 'join', 'where'
#         ]

#     def classify(self, query: QueryRequest) -> Tuple[QueryType, str]:
#         try:
#             query_lower = query.text.lower()


#             if "detailed" in query_lower or "with details" in query_lower:
#                 query.detailed = True
            
#             # Check for simple patterns first
#             for pattern_group in self.simple_patterns.values():
#                 for pattern in pattern_group:
#                     if re.search(pattern, query_lower):
#                         return (QueryType.SIMPLE, "matches_simple_pattern")
                    
            
#             # Check for complex indicators
#             if any(indicator in query_lower for indicator in self.complex_indicators):
#                 return (QueryType.COMPLEX, "contains_complex_indicators")
                
#             # Default to simple for unknown queries
#             return (QueryType.SIMPLE, "default_simple")
#         except Exception as e:
#             # Return complex type if classification fails
#             return (QueryType.COMPLEX, f"classification_error: {str(e)}")
import re
from enum import Enum
from typing import Tuple
from core.models.query import QueryRequest, QueryType
from typing import Tuple
from core.models.query import QueryRequest, QueryType
from core.services.gemini_classifier import GeminiClassifier

class QueryClassifier:
    def __init__(self, gemini_api_key: str = None):
        self.gemini = GeminiClassifier(gemini_api_key) if gemini_api_key else None
        # Keep regex as fallback
        self.simple_patterns = {
            "list_vms": [r"list vms", r"show instances"],
            "vm_details": [r"details for vm (\S+)"]
        }

    def classify(self, query: QueryRequest) -> Tuple[QueryType, str]:
        # Try Gemini first if available
        if self.gemini:
            try:
                result = self.gemini.classify(query.text)
                if result["query_type"] == "simple":
                    query.filters.update(result.get("parameters", {}).get("filters", {}))
                    return (QueryType.SIMPLE, result["intent"])
                return (QueryType.COMPLEX, result["intent"])
            except Exception:
                pass  # Fall through to regex

        # Regex fallback
        return self._classify_with_regex(query)

    def _classify_with_regex(self, query: QueryRequest) -> Tuple[QueryType, str]:
        query_lower = query.text.lower()
        for intent, patterns in self.simple_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return (QueryType.SIMPLE, intent)
        return (QueryType.COMPLEX, "regex_fallback")