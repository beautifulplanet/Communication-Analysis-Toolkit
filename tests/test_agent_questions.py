"""
================================================================================
Communication Analysis Toolkit — Agent Test Suite (200+ Questions)
================================================================================

Comprehensive test suite for the AI Analysis Agent covering:
  - Layer 1: Structured stat queries (counts, comparisons, breakdowns)
  - Layer 2: RAG retrieval + local analysis (context-based, filtering)
  - Edge cases: ambiguous questions, empty results, boundary conditions
  - Regression: questions that previously caused bugs

Each test verifies:
  1. The agent returns a non-empty answer
  2. The answer is routed to the correct layer
  3. Key expected terms appear in the answer

Run:
    pytest tests/test_agent_questions.py -v
================================================================================
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Imports under test
# ---------------------------------------------------------------------------
from api.agent import AgentAnswer, AnalysisAgent
from api.retriever import MessageRetriever
from engine.db import init_db
from engine.storage import CaseStorage

# ---------------------------------------------------------------------------
# Fixture: load sample DATA.json and build a test SQLite database
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sample_data() -> dict[str, Any]:
    """Load the generated sample DATA.json."""
    path = Path("cases/sample/output/DATA.json")
    if not path.exists():
        pytest.skip("Sample DATA.json not found — run: python -m tools.generate_sample_data")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def agent(sample_data: dict[str, Any]) -> AnalysisAgent:
    """Create an agent backed by a temp SQLite DB loaded from sample data."""
    tmp_dir = tempfile.mkdtemp()
    db_path = Path(tmp_dir) / "test_agent.db"
    init_db(db_path)
    storage = CaseStorage(db_path)

    case_id = storage.create_case(
        name=sample_data.get("case", "Test Case"),
        user_name=sample_data.get("user", "User"),
        contact_name=sample_data.get("contact", "Contact"),
    )

    for date_str, day in sample_data.get("days", {}).items():
        for msg in day.get("messages", []):
            msg_id = storage.add_message(case_id, {
                "timestamp": msg.get("timestamp", 0),
                "date": date_str,
                "time": msg.get("time", ""),
                "source": "test",
                "direction": msg.get("direction", "unknown"),
                "body": msg.get("body", ""),
            })
            labels = msg.get("labels", {})
            if labels:
                storage.add_analysis(msg_id, {
                    "is_hurtful": labels.get("severity") is not None,
                    "severity": labels.get("severity"),
                    "is_apology": labels.get("is_apology", False),
                    "patterns": labels.get("patterns", []),
                    "keywords": labels.get("keywords", []),
                    "supportive": labels.get("supportive", []),
                })

    return AnalysisAgent(
        storage, case_id,
        user_name=sample_data.get("user", "User"),
        contact_name=sample_data.get("contact", "Contact"),
    )


@pytest.fixture(scope="module")
def retriever(sample_data: dict[str, Any]) -> MessageRetriever:
    """Create a retriever from sample data."""
    return MessageRetriever(sample_data)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def assert_answer(
    answer: AgentAnswer,
    *,
    contains: list[str] | None = None,
    layer: int | None = None,
    not_empty: bool = True,
) -> None:
    """Assert common properties of an agent answer."""
    if not_empty:
        assert answer.answer, "Answer should not be empty"
        assert len(answer.answer.strip()) > 0
    if layer is not None:
        assert answer.layer == layer, f"Expected layer {layer}, got {answer.layer}"
    if contains:
        lower_answer = answer.answer.lower()
        for term in contains:
            assert term.lower() in lower_answer, (
                f"Expected '{term}' in answer, got: {answer.answer[:200]}"
            )


# ===========================================================================
# SECTION 1: LAYER 1 — Structured Stat Queries (40 tests)
# ===========================================================================


class TestMessageCounts:
    """Questions about message volume."""

    def test_total_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many messages total?"), layer=1, contains=["total"])

    def test_how_many_messages_sent(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many messages were sent?"), layer=1)

    def test_message_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What's the message count?"), layer=1)

    def test_number_of_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Tell me the number of messages"), layer=1)

    def test_total_messages_exchanged(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many total messages were exchanged?"), layer=1)


class TestDayCounts:
    """Questions about time periods."""

    def test_how_many_days(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many days?"), layer=1, contains=["days"])

    def test_total_days(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Total days in the analysis"), layer=1)

    def test_how_long(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How long was the relationship analyzed?"), layer=1)

    def test_number_of_days(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Number of days in the dataset"), layer=1)

    @pytest.mark.xfail(reason="Planned: L1 handler needs contact-day enrichment")
    def test_days_with_contact(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("How many days had contact?")
        assert_answer(ans, layer=1, contains=["contact"])


class TestHurtfulCounts:
    """Questions about hurtful language counts."""

    def test_how_many_hurtful(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many hurtful messages were there?"), layer=1)

    def test_hurtful_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What's the hurtful count?"), layer=1)

    def test_hurtful_instances(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many times was hurtful language used?"))

    @pytest.mark.xfail(reason="Planned: L1 hurtful by-party breakdown")
    def test_hurtful_breakdown_user_contact(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("How many hurtful messages from each person?")
        assert_answer(ans, layer=1, contains=["alex", "jordan"])


class TestPatternCounts:
    """Questions about specific pattern counts."""

    def test_gaslighting_count(self, agent: AnalysisAgent) -> None:
        assert_answer(
            agent.ask("How many times did gaslighting happen?"),
            layer=1, contains=["gaslighting"],
        )

    def test_darvo_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How often was DARVO used?"), layer=1, contains=["darvo"])

    def test_guilt_trip_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many instances of guilt trips?"), layer=1)

    def test_love_bombing_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many times was love bombing detected?"), layer=1)

    def test_stonewalling_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How often did stonewalling occur?"), layer=1)

    def test_triangulation_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Count of triangulation instances"), layer=1)

    def test_deflection_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many times was deflection used?"), layer=1)

    def test_minimizing_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Instances of minimizing behavior"), layer=1)

    def test_contempt_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many instances of contempt?"), layer=1)

    def test_blame_shifting_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How often did blame shifting happen?"), layer=1)

    def test_future_faking_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Instances of future faking"), layer=1)

    def test_silent_treatment_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many times was silent treatment threatened?"), layer=1)

    def test_reverse_victim_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How often did reverse victim occur?"), layer=1)

    def test_coercive_control_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many instances of coercive control?"), layer=1)

    def test_criticism_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many instances of criticism?"), layer=1)

    def test_deny_count(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How often did deny happen?"), layer=1)


class TestComparisons:
    """Who-sent-more / who-was-worse questions."""

    def test_who_sent_more(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Who sent more messages?"), layer=1)

    def test_who_messaged_more(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Who messaged more?"), layer=1)

    def test_who_texted_more(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Who texted more?"), layer=1)

    def test_who_was_worse(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Who was worse overall?"), layer=1)

    def test_who_was_more_hurtful(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Who was more hurtful?"), layer=1)

    def test_who_was_meaner(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Who was meaner?"), layer=1)


class TestWorstDay:
    """Worst-day questions."""

    def test_worst_day(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What was the worst day?"), layer=1, contains=["worst day"])

    def test_most_hurtful_day(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What was the most hurtful day?"), layer=1)

    def test_most_conflict(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("When was the most conflict?"), layer=1)


class TestCallStats:
    """Phone call related questions."""

    def test_how_many_calls(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many calls were made?"), layer=1, contains=["calls"])

    def test_call_duration(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What was the total call duration?"), layer=1)

    def test_phone_calls(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many phone calls?"), layer=1)

    def test_talk_time(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How much talk time?"), layer=1)


class TestNoContactDays:
    """Silent/no-contact questions."""

    def test_no_contact_days(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many days without contact?"), layer=1)

    @pytest.mark.xfail(reason="Planned: L1 silent day detection")
    def test_silent_days(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many silent days?"), layer=1)


class TestBreakdowns:
    """Pattern/severity breakdown questions."""

    def test_pattern_breakdown(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What patterns were detected?"), layer=1)

    def test_which_patterns(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Which patterns appeared?"), layer=1)

    def test_list_patterns(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Can you list patterns?"), layer=1)

    def test_types_of_patterns(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What types of patterns were found?"), layer=1)

    def test_severity_breakdown(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What's the severity breakdown?"), layer=1)

    def test_how_severe(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How severe was the language?"), layer=1)

    def test_severity_distribution(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show the severity distribution"), layer=1)

    @pytest.mark.xfail(reason="Planned: L1 top-pattern ranking handler")
    def test_top_pattern(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What was the most common pattern?"), layer=1)

    @pytest.mark.xfail(reason="Planned: L1 top-pattern ranking handler")
    def test_main_pattern(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What's the main pattern?"), layer=1)


@pytest.mark.xfail(reason="Planned: L1 gap detection handler")
class TestGaps:
    """Communication gap questions."""

    def test_communication_gaps(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Were there any communication gaps?"), layer=1)

    def test_longest_gap(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What was the longest gap?"), layer=1)

    def test_no_contact_periods(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show no contact periods"), layer=1)


@pytest.mark.xfail(reason="Planned: L1 monthly aggregation handler")
class TestMonthly:
    """Monthly breakdown questions."""

    def test_monthly_breakdown(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show the monthly breakdown"), layer=1)

    def test_per_month(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Give me stats per month"), layer=1)

    def test_each_month(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What happened each month?"), layer=1)

    def test_month_by_month(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me month by month"), layer=1)


# ===========================================================================
# SECTION 2: LAYER 2 — RAG Retrieval + Context (80 tests)
# ===========================================================================


class TestApologyQueries:
    """Questions about apologies."""

    def test_did_they_apologize(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Did Jordan ever apologize?"), layer=2)

    def test_genuine_apologies(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Were any apologies genuine?"), layer=2)

    def test_how_many_apologies(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many times did they say sorry?"), layer=2)

    def test_apology_after_fight(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Did she apologize after the fights?"), layer=2)

    def test_sincere_apology(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was the apology sincere or dismissive?"), layer=2)


class TestHurtfulContextQueries:
    """Questions that need actual message context about hurtful content."""

    def test_show_hurtful_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me the hurtful messages"), layer=2)

    def test_mean_things_said(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What mean things were said?"), layer=2)

    def test_cruel_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me the cruel messages"), layer=2)

    def test_abusive_language(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was there abusive language?"), layer=2)

    def test_toxic_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me all toxic messages"), layer=2)

    def test_worst_things_said(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What were the worst things said?"), layer=2)

    def test_severe_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me only severe messages"), layer=2)

    def test_moderate_hurtful(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show moderate hurtful messages"), layer=2)


class TestPatternContextQueries:
    """Questions about specific patterns with context."""

    def test_show_gaslighting(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me the gaslighting messages"), layer=2)

    def test_darvo_examples(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Give me examples of DARVO"), layer=2)

    def test_guilt_trip_examples(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show guilt trip instances"), layer=2)

    def test_love_bombing_examples(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show love bombing messages"), layer=2)

    def test_stonewalling_examples(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Find stonewalling behavior"), layer=2)

    def test_manipulation_examples(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me manipulation tactics used"), layer=2)

    def test_contempt_examples(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show contempt messages"), layer=2)

    def test_deflection_examples(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show deflection messages"), layer=2)

    def test_minimizing_examples(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show minimizing behavior"), layer=2)

    def test_triangulation_examples(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show triangulation instances"), layer=2)


class TestDateFilteredQueries:
    """Questions filtered by date or month."""

    def test_what_happened_in_june(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What happened in June?"), layer=2)

    def test_july_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me July messages"), layer=2)

    def test_august_hurtful(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Were there mean messages in August?"), layer=2)

    def test_specific_date(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What happened on 2025-06-15?"), layer=2)

    def test_date_range(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show messages from 2025-06-01 to 2025-06-15"), layer=2)

    def test_june_gaslighting(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was there gaslighting in June?"), layer=2)

    def test_jul_patterns(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show messages with manipulation from Jul"), layer=2)


class TestDirectionQueries:
    """Questions about who said what."""

    def test_what_jordan_said(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What did Jordan say that was hurtful?"), layer=2)

    def test_alex_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show my messages that were hurtful"), layer=2)

    def test_she_said(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What hurtful things she said"), layer=2)

    def test_i_said(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show what I said that was hurtful"), layer=2)

    def test_contact_patterns(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What manipulation did Jordan use?"), layer=2)


class TestKeywordQueries:
    """Keyword-based search queries."""

    def test_search_love(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Find messages about love"), layer=2)

    def test_search_dinner(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Find messages about dinner"), layer=2)

    def test_search_sorry(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Find all messages containing sorry"), layer=2)

    def test_search_miss(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Messages where someone said miss"), layer=2)

    def test_search_crazy(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Find messages with the word crazy"), layer=2)


class TestComplexContextQueries:
    """Complex questions requiring message context understanding."""

    def test_escalation_pattern(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Did things get worse over time?"), layer=2)

    def test_good_days(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Were there any good days?"), layer=2)

    def test_nice_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me nice messages"), layer=2)

    def test_morning_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What did morning messages look like?"), layer=2)

    def test_goodnight_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Find goodnight messages"), layer=2)

    def test_i_love_you_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many times was 'I love you' said?"), layer=2)

    def test_fight_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me messages from fights"), layer=2)

    def test_de_escalation_attempts(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Did anyone try to calm things down?"), layer=2)

    def test_name_calling(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was there any name calling?"), layer=2)

    def test_insults(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me all insults"), layer=2)


class TestRelationshipDynamicsQueries:
    """Questions about relationship dynamics."""

    def test_who_started_fights(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Who usually started the fights?"), layer=2)

    def test_after_conflict(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What happened after conflicts?"), layer=2)

    def test_cycle_of_abuse(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was there a cycle of abuse?"), layer=2)

    def test_love_then_hate(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Did they go from love bombing to being mean?"), layer=2)

    def test_manipulation_tactics(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What manipulation tactics were most common?"), layer=2)


class TestMiscContextQueries:
    """Miscellaneous contextual queries."""

    def test_emoji_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show messages with hearts"), layer=2)

    def test_question_messages(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What questions did they ask?"), layer=2)

    def test_threats(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Were there any threats?"), layer=2)

    def test_putting_down(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Did they put each other down?"), layer=2)

    def test_controlling_behavior(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was there controlling behavior?"), layer=2)


# ===========================================================================
# SECTION 3: EDGE CASES & UNPREDICTABLE QUESTIONS (60 tests)
# ===========================================================================


class TestAmbiguousQuestions:
    """Vague or ambiguous questions that real users would ask."""

    def test_was_it_bad(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was it bad?"))

    def test_is_this_normal(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Is this normal?"))

    def test_what_should_i_know(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What should I know?"))

    def test_summary_please(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Just give me a summary"))

    def test_how_bad_was_it(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How bad was it?"))

    def test_tell_me_everything(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Tell me everything"))

    def test_whats_the_verdict(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What's the verdict?"))

    def test_single_word_help(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Help"))

    def test_single_word_summary(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Summary"))

    def test_what_happened(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("What happened?"))


class TestEmotionalQuestions:
    """Questions asked from an emotional state."""

    def test_was_i_the_problem(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was I the problem?"))

    def test_did_they_ever_love_me(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Did they ever love me?"))

    def test_am_i_crazy(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Am I crazy or was this abusive?"))

    def test_was_it_my_fault(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was it my fault?"))

    def test_should_i_go_back(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Should I go back to them?"))

    def test_why_did_they_do_this(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Why did they do this to me?"))

    def test_all_my_fault(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("They always said it was all my fault"))

    def test_confused_about_feelings(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("I'm confused about what's real"))

    def test_was_it_really_that_bad(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was it really that bad or am I exaggerating?"))

    def test_they_said_im_too_sensitive(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("They always said I'm too sensitive"))


class TestGrammaticalVariations:
    """Same question asked in different ways."""

    def test_gaslight_v1(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How many gaslighting instances?"))

    def test_gaslight_v2(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Count the gaslighting"))

    def test_gaslight_v3(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("gaslighting count"))

    def test_gaslight_v4(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Was there gaslighting?"))

    def test_gaslight_v5(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("tell me about the gaslighting"))

    def test_hurtful_v1(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("hurtful stuff"))

    def test_hurtful_v2(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("mean things"))

    def test_hurtful_v3(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("any nasty messages?"))

    def test_hurtful_v4(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("show the bad messages"))

    def test_hurtful_v5(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("toxic things said"))


class TestTyposAndCasual:
    """Questions with typos, slang, or casual language."""

    def test_typo_gaslihgting(self, agent: AnalysisAgent) -> None:
        # Typo - agent should still try to find something
        ans = agent.ask("any gaslihgting?")
        assert ans.answer  # Should return something even with typo

    def test_casual_yo_whats_up(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("yo so like what even happened")
        assert ans.answer

    def test_all_caps(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("HOW MANY MESSAGES"))

    def test_no_punctuation(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("total messages sent and received"))

    def test_extra_spaces(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("  how  many  hurtful  messages  "))

    def test_mixed_case(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("How Many DARVO instances"))

    def test_informal(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("lol so did they actually gaslight me")
        assert ans.answer

    def test_super_short(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("hurtful?")
        assert ans.answer

    def test_question_mark_only(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("??")
        assert ans.answer  # Should not crash


class TestBoundaryConditions:
    """Edge cases and boundary conditions."""

    def test_empty_question(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("")
        assert ans.answer  # Should handle gracefully

    def test_very_long_question(self, agent: AnalysisAgent) -> None:
        long_q = "Can you show me " + "all the " * 50 + "messages?"
        ans = agent.ask(long_q)
        assert ans.answer

    def test_special_characters(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("What about <script>alert('xss')</script>?")
        assert ans.answer  # Should not crash

    def test_sql_injection_attempt(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("'; DROP TABLE messages; --")
        assert ans.answer  # Should handle safely

    def test_unicode_question(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("Show me messages with emojis and unicode chars")
        assert ans.answer

    def test_numbers_in_question(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show messages from day 1 to day 30"))


class TestCombinedFilters:
    """Questions that combine multiple filter criteria."""

    def test_june_gaslighting_from_contact(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Gaslighting from Jordan in June"), layer=2)

    def test_severe_in_july(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Show me severe hurtful messages from July"), layer=2)

    def test_hurtful_from_user_august(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("My hurtful messages in August"), layer=2)

    def test_apology_in_june(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("Did they apologize in June?"), layer=2)

    def test_darvo_from_contact(self, agent: AnalysisAgent) -> None:
        assert_answer(agent.ask("DARVO instances from Jordan"), layer=2)


class TestUncommonQuestions:
    """Unusual questions that real users might ask."""

    def test_percentages(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("What percentage of messages were hurtful?")
        assert ans.answer

    def test_ratio_question(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("What's the ratio of good to bad messages?")
        assert ans.answer

    def test_trend_question(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("Is there a trend in the hurtful messages?")
        assert ans.answer

    def test_prediction_question(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("Would things have gotten worse?")
        assert ans.answer

    def test_comparison_to_normal(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("Is this amount of conflict normal?")
        assert ans.answer

    def test_advice_question(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("What should I do about this?")
        assert ans.answer

    def test_legal_question(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("Can I use this as evidence in court?")
        assert ans.answer

    def test_therapy_question(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("Should I bring this to therapy?")
        assert ans.answer

    def test_specific_quote(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("Did they ever say 'you're crazy'?")
        assert ans.answer

    def test_conversation_flow(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("How did conversations usually flow?")
        assert ans.answer


# ===========================================================================
# SECTION 4: RETRIEVER UNIT TESTS (30 tests)
# ===========================================================================


class TestRetrieverDateFilter:
    """Test the retriever's date filtering."""

    def test_filter_by_month(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(date_start="2025-06-01", date_end="2025-06-30")
        assert result.count > 0
        for m in result.messages:
            assert m.time.startswith("2025-06")

    def test_filter_by_exact_date(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(date_start="2025-07-01", date_end="2025-07-01")
        for m in result.messages:
            assert m.time.startswith("2025-07-01")

    def test_filter_future_date(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(date_start="2030-01-01")
        assert result.count == 0


class TestRetrieverPatternFilter:
    """Test the retriever's pattern filtering."""

    def test_filter_gaslighting(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(patterns=["gaslighting"])
        for m in result.messages:
            assert "gaslighting" in [p.lower() for p in m.labels.get("patterns", [])]

    def test_filter_multiple_patterns(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(patterns=["gaslighting", "darvo"])
        for m in result.messages:
            pats = {p.lower() for p in m.labels.get("patterns", [])}
            assert pats & {"gaslighting", "darvo"}

    def test_filter_nonexistent_pattern(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(patterns=["nonexistent_pattern_xyz"])
        assert result.count == 0


class TestRetrieverDirectionFilter:
    """Test the retriever's direction filtering."""

    def test_filter_user(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(direction="user")
        for m in result.messages:
            assert "user" in m.direction.lower()

    def test_filter_contact(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(direction="contact")
        for m in result.messages:
            assert "contact" in m.direction.lower()


class TestRetrieverSeverityFilter:
    """Test the retriever's severity filtering."""

    def test_filter_severe(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(severity="severe")
        for m in result.messages:
            assert m.labels.get("severity") == "severe"

    def test_filter_moderate(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(severity="moderate")
        for m in result.messages:
            assert m.labels.get("severity") == "moderate"

    def test_filter_mild(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(severity="mild")
        for m in result.messages:
            assert m.labels.get("severity") == "mild"


class TestRetrieverKeywordFilter:
    """Test the retriever's keyword search."""

    def test_keyword_love(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(keywords=["love"])
        for m in result.messages:
            assert "love" in m.body.lower()

    def test_keyword_dinner(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(keywords=["dinner"])
        for m in result.messages:
            assert "dinner" in m.body.lower()

    def test_keyword_no_match(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(keywords=["xyznonexistent123"])
        assert result.count == 0

    def test_multiple_keywords(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(keywords=["love", "miss"])
        for m in result.messages:
            body = m.body.lower()
            assert "love" in body or "miss" in body


class TestRetrieverApologyFilter:
    """Test the retriever's apology filtering."""

    def test_filter_apologies(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(is_apology=True)
        for m in result.messages:
            assert m.labels.get("is_apology") is True

    def test_filter_non_apologies(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(is_apology=False)
        for m in result.messages:
            assert m.labels.get("is_apology") is not True


class TestRetrieverHurtfulFilter:
    """Test the retriever's hurtful filtering."""

    def test_filter_hurtful_only(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(is_hurtful=True)
        for m in result.messages:
            assert m.labels.get("severity") is not None

    def test_filter_non_hurtful(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(is_hurtful=False)
        for m in result.messages:
            assert m.labels.get("severity") is None


class TestRetrieverLimit:
    """Test the retriever's limit behavior."""

    def test_limit_10(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(limit=10)
        assert result.count <= 10

    def test_limit_1(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve(limit=1)
        assert result.count <= 1

    def test_default_limit(self, retriever: MessageRetriever) -> None:
        result = retriever.retrieve()
        assert result.count <= 200


class TestRetrieverSearch:
    """Test the smart search method."""

    def test_search_june(self, retriever: MessageRetriever) -> None:
        result = retriever.search("Show me June messages")
        assert "from=2025-06-01" in str(result.filters_applied)

    def test_search_gaslighting(self, retriever: MessageRetriever) -> None:
        result = retriever.search("gaslighting instances")
        assert "patterns=" in str(result.filters_applied)

    def test_search_hurtful(self, retriever: MessageRetriever) -> None:
        result = retriever.search("show me mean messages")
        assert "is_hurtful=True" in str(result.filters_applied)

    def test_search_apology(self, retriever: MessageRetriever) -> None:
        result = retriever.search("did they apologize")
        assert "is_apology=True" in str(result.filters_applied)

    def test_search_contact_direction(self, retriever: MessageRetriever) -> None:
        result = retriever.search("what she said that was hurtful")
        assert "direction=contact" in str(result.filters_applied)

    def test_search_user_direction(self, retriever: MessageRetriever) -> None:
        result = retriever.search("show what I said")
        assert "direction=user" in str(result.filters_applied)

    def test_search_severe(self, retriever: MessageRetriever) -> None:
        result = retriever.search("show severe messages only")
        assert "severity=severe" in str(result.filters_applied)


# ===========================================================================
# SECTION 5: AGENT INTEGRATION TESTS (20 tests)
# ===========================================================================


class TestAgentIntegration:
    """End-to-end tests verifying agent behavior."""

    def test_layer1_returns_numeric_data(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("How many messages total?")
        assert ans.layer == 1
        assert any(c.isdigit() for c in ans.answer)

    def test_layer2_returns_evidence(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("Show me all toxic messages")
        assert ans.layer == 2
        # Should have evidence if hurtful messages exist
        if "Found" in ans.answer and "0" not in ans.answer[:20]:
            assert len(ans.evidence) > 0 or "Key messages:" in ans.answer

    def test_ask_with_prompt_returns_both(self, agent: AnalysisAgent) -> None:
        ans, prompt = agent.ask_with_prompt("What happened in June?")
        assert ans.answer
        assert len(prompt) > 100
        assert "Question:" in prompt

    @pytest.mark.xfail(reason="Planned: L2 retriever SQLite integration")
    def test_prompt_contains_messages(self, agent: AnalysisAgent) -> None:
        _, prompt = agent.ask_with_prompt("Show gaslighting examples")
        assert "User" in prompt or "Contact" in prompt

    def test_prompt_has_system_instruction(self, agent: AnalysisAgent) -> None:
        _, prompt = agent.ask_with_prompt("Any question here")
        assert "analyzing communication" in prompt.lower()

    def test_structured_answers_are_deterministic(self, agent: AnalysisAgent) -> None:
        a1 = agent.ask("How many messages total?")
        a2 = agent.ask("How many messages total?")
        assert a1.answer == a2.answer

    def test_different_questions_different_answers(self, agent: AnalysisAgent) -> None:
        a1 = agent.ask("How many messages?")
        a2 = agent.ask("Who was worse?")
        assert a1.answer != a2.answer

    def test_all_layer1_high_confidence(self, agent: AnalysisAgent) -> None:
        for q in ["How many messages?", "Who sent more?", "Worst day?"]:
            ans = agent.ask(q)
            if ans.layer == 1:
                assert ans.confidence >= 0.5

    def test_user_label_in_answers(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("Who sent more messages?")
        assert "alex" in ans.answer.lower() or "jordan" in ans.answer.lower()

    @pytest.mark.xfail(reason="Planned: L2 retriever SQLite integration")
    def test_retrieval_metadata(self, agent: AnalysisAgent) -> None:
        ans = agent.ask("Show toxic messages")
        if ans.retrieval:
            assert ans.retrieval.total_searched > 0

    def test_no_crash_on_rapid_questions(self, agent: AnalysisAgent) -> None:
        questions = [
            "messages?", "hurtful?", "patterns?", "calls?",
            "who?", "worst?", "gaps?", "monthly?", "severity?",
            "gaslighting?",
        ]
        for q in questions:
            ans = agent.ask(q)
            assert ans.answer  # None of them should crash


class TestAgentWithEmptyData:
    """Test agent with empty or minimal dataset."""

    @staticmethod
    def _make_agent(tmp_path: Path, name: str = "Test") -> AnalysisAgent:
        """Create a minimal agent backed by an empty SQLite DB."""
        db_path = tmp_path / f"{name}.db"
        init_db(db_path)
        storage = CaseStorage(db_path)
        case_id = storage.create_case(name=name, user_name="A", contact_name="B")
        return AnalysisAgent(storage, case_id, user_name="A", contact_name="B")

    def test_empty_days(self, tmp_path: Path) -> None:
        agent = self._make_agent(tmp_path, "Empty")
        ans = agent.ask("How many messages total?")
        assert "0" in ans.answer

    @pytest.mark.xfail(reason="Planned: empty data edge case refinement")
    def test_no_hurtful_messages(self, tmp_path: Path) -> None:
        agent = self._make_agent(tmp_path, "Peaceful")
        ans = agent.ask("Who was worse?")
        assert "equal" in ans.answer.lower() or "0" in ans.answer

    def test_no_patterns(self, tmp_path: Path) -> None:
        agent = self._make_agent(tmp_path, "NoPatterns")
        ans = agent.ask("What patterns were detected?")
        assert "no" in ans.answer.lower()

    @pytest.mark.xfail(reason="Planned: empty data edge case refinement")
    def test_no_gaps(self, tmp_path: Path) -> None:
        agent = self._make_agent(tmp_path, "NoGaps")
        ans = agent.ask("Were there any communication gaps?")
        assert "no" in ans.answer.lower()
