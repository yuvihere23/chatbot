import pytest
from core.services.query_classifier import QueryClassifier
from core.models.query import QueryRequest, QueryType

@pytest.fixture
def classifier():
    return QueryClassifier()

def test_simple_query_classification(classifier):
    query = QueryRequest(text="list all vms", cloud="aws")
    query_type, reason = classifier.classify(query)
    assert query_type == QueryType.SIMPLE
    assert "matched_simple_pattern" in reason

def test_complex_query_classification(classifier):
    query = QueryRequest(text="show vms with cpu < 20%", cloud="azure")
    query_type, reason = classifier.classify(query)
    assert query_type == QueryType.COMPLEX
    assert "contains_complex_indicators" in reason