
from api.utils import extract_date_range


def test_extraction():
    q = "show me messages in june 2025"
    print(f"Query: {q}")
    res = extract_date_range(q)
    print(f"Result: {res}")

    q2 = "messages in 2024"
    print(f"Query: {q2}")
    res2 = extract_date_range(q2)
    print(f"Result: {res2}")

    q3 = "june"
    print(f"Query: {q3}")
    res3 = extract_date_range(q3)
    print(f"Result: {res3}")

if __name__ == "__main__":
    test_extraction()
