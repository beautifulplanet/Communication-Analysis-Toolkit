"""
================================================================================
Test Suite: Malformed Data Resilience
================================================================================

Verifies that the Agent and Retriever degrade gracefully when encountering
corrupt, missing, or malformed data in DATA.json.

The agent should NEVER crash. It should skip bad data and return whatever
valid information remains, or a polite fallback message.
================================================================================
"""

from typing import Any

from api.agent import AnalysisAgent


class TestRetrieverResilience:
    """Test that the retriever skips bad data without crashing."""

    def test_skip_malformed_day(self) -> None:
        """A day that isn't a dict should be skipped."""
        data: dict[str, Any] = {
            "days": {
                "2025-01-01": "this is a string, not a dict",  # <--- MALFORMED
                "2025-01-02": {"messages": [{"time": "T", "direction": "u", "body": "test message content"}]}
            }
        }
        agent = AnalysisAgent(data)

        # 1. L1 attempts sum -> crashes on str.get() -> catches Exception -> returns None
        # 2. Falls to L2 -> retriever.search("test message") -> finds the valid message
        # 3. Returns summary
        ans = agent.ask("test message")
        assert "1" in ans.answer

    def test_skip_malformed_message_list(self) -> None:
        """A day where 'messages' is not a list."""
        data: dict[str, Any] = {
            "days": {
                "2025-01-01": {"messages": "not a list"},  # <--- MALFORMED
            }
        }
        agent = AnalysisAgent(data)
        ans = agent.ask("count messages")
        # L1 returns None if count is 0, falling back to L2.
        # L2 searches for "count messages", finds nothing, returns "Couldn't find..."
        assert "couldn't find" in ans.answer.lower()

    def test_skip_malformed_individual_message(self) -> None:
        """A single message that is missing keys or wrong type."""
        data: dict[str, Any] = {
            "days": {
                "2025-01-01": {
                    "messages": [
                        {"time": "T1", "direction": "u", "body": "msg one"},
                        "this string is not a message dict",  # <--- MALFORMED
                        {"time": "T2", "direction": "c", "body": "msg two"},
                    ]
                }
            }
        }
        agent = AnalysisAgent(data)
        # Search for "msg" to match the body "msg one" (keyword match)
        ans = agent.ask("show me msg")
        # Retriever should strip the string, leaving 2 valid messages
        assert "2" in ans.answer

    def test_layer1_fallback_on_missing_keys(self) -> None:
        """Layer 1 relies on 'messages_sent' key. If missing, it returns 0 (safe)."""
        data: dict[str, Any] = {
            "days": {
                "2025-01-01": {
                    "messages": [{"time": "T", "direction": "u", "body": "msg"}]
                    # Missing 'messages_sent'
                }
            }
        }
        agent = AnalysisAgent(data)
        ans = agent.ask("How many messages total?")
        # It safely returns 0 because we used .get("messages_sent", 0)
        assert "0" in ans.answer

    def test_total_garbage_input(self) -> None:
        """Test with a completely empty/garbage dataset."""
        data: dict[str, Any] = {"random": "garbage"}
        agent = AnalysisAgent(data)

        # Should not crash
        ans = agent.ask("Anything happened?")
        assert ans.answer
        assert ans.layer  # Just check it has a layer

    def test_none_values_in_message(self) -> None:
        """Test explicit None values where strings are expected."""
        data: dict[str, Any] = {
            "days": {
                "2025-01-01": {
                    "messages": [
                        {
                            "time": None,
                            "direction": None,
                            "body": "content",
                            "labels": None
                        }
                    ]
                }
            }
        }
        agent = AnalysisAgent(data)
        ans = agent.ask("content")
        # Should find the message because body matches
        assert "1" in ans.answer
