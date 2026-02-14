
import pytest

from api.agent import AnalysisAgent
from api.dependencies import load_case_data

# Expected answers for cases/sample/output/DATA.json
# Format: (question, expected_substring, min_confidence)
GOLDEN_QA = [
    # Metadata
    ("Who is the user?", "Alex", 0.9),
    ("Who is the contact?", "Jordan", 0.9),
    ("When does the data start?", "2025-06-01", 0.8),

    # Quantitative (L1) - Global stats (date filtering not yet supported)
    ("How many messages were sent?", "607", 0.9),
    ("How many messages were received?", "647", 0.9),
    ("Total messages?", "1,254", 0.9),

    # Pattern Detection
    ("Did Jordan gaslight me?", "gaslighting", 0.7),
    ("Did Alex gaslight Jordan?", "Alex: 0", 0.7), # Alex has 0 patterns in sample snippet

    # Specific Content (Retrieval)
    ("Who mentioned milk?", "milk", 0.7),
    ("What did Jordan say about being the bad guy?", "bad guy", 0.7),
]

@pytest.fixture(scope="module")
def agent():
    """Load the sample agent once for all tests."""
    try:
        data = load_case_data("sample")
        return AnalysisAgent(data)
    except Exception as e:
        pytest.skip(f"Could not load sample data: {e}")

@pytest.mark.parametrize(("question", "expected", "min_conf"), GOLDEN_QA)
def test_golden_answer(agent, question, expected, min_conf):
    result = agent.ask(question)

    # Check answer content
    # Check answer content
    if expected.lower() not in result.answer.lower():
         with open("debug_failure.txt", "w", encoding="utf-8") as f:
             f.write(f"Question: {question}\nExpected: {expected}\nActual: {result.answer}\nConfidence: {result.confidence}\nLayer: {result.layer}\nRetrieval: {result.retrieval}\n")
    assert expected.lower() in result.answer.lower(), \
        f"Question: {question}\nExpected '{expected}' in answer:\n{result.answer}"

    # Check confidence
    assert result.confidence >= min_conf, \
        f"Question: {question}\nConfidence {result.confidence} < {min_conf}"
