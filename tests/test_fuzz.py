
import random
import string

import pytest

from api.agent import AnalysisAgent
from api.dependencies import load_case_data


@pytest.fixture(scope="module")
def agent():
    """Load the sample agent once for all tests."""
    try:
        data = load_case_data("sample")
        return AnalysisAgent(data)
    except Exception as e:
        pytest.skip(f"Could not load sample data: {e}")

def generate_random_string(length: int) -> str:
    """Generate a random string of fixed length."""
    letters = string.ascii_letters + string.digits + string.punctuation + " "
    return ''.join(random.choice(letters) for i in range(length))

def test_fuzz_agent_ask(agent):
    """Fuzz test the agent.ask method with random inputs."""
    # Seed for reproducibility
    random.seed(42)

    inputs = [
        "",  # Empty
        "   ",  # Whitespace
        "a" * 1000,  # Long
        "???????", # Punctuation
        "\n\t\r", # Control chars
        "😊" * 10, # Unicode
        "None", # String "None"
        "null",
        "undefined",
    ]

    # Add random strings
    for _ in range(50):
        inputs.append(generate_random_string(random.randint(1, 200)))

    for q in inputs:
        # Should never raise
        try:
            answer = agent.ask(q)

            # Check invariants
            assert isinstance(answer.answer, str)
            assert 0.0 <= answer.confidence <= 1.0
            assert answer.layer in [0, 1, 2, 3]

            # If layer 0 (error), confidence should be low
            if answer.layer == 0:
                assert answer.confidence == 0.0

        except Exception as e:
            pytest.fail(f"Agent crashed on input {q!r}: {e}")
