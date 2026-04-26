#!/usr/bin/env python3
"""
Automated tests for RAG (Retrieval-Augmented Generation) components.
Tests reliability, accuracy, and consistency of the RAG system.
"""

import pytest
from datetime import datetime, timedelta
from pawpal_system import (
    RagRetriever, AiCareCoach, EnhancedScheduler,
    Owner, Pet, Task
)


class TestRagRetriever:
    """Test the RAG retrieval system."""

    def test_retriever_loads_documents(self):
        """Verify that documents are loaded from the docs directory."""
        retriever = RagRetriever()
        assert len(retriever.documents) > 0, "No documents loaded"
        assert any('priorit' in name.lower() for name in retriever.documents.keys()), \
            "Priorities document not found"

    def test_retriever_returns_dict_structure(self):
        """Verify retriever returns expected dictionary structure."""
        retriever = RagRetriever()
        result = retriever.retrieve("feeding priority")

        assert isinstance(result, dict), "Retrieval should return a dictionary"
        assert 'query' in result, "Missing 'query' key"
        assert 'matched_documents' in result, "Missing 'matched_documents' key"
        assert 'consolidated_info' in result, "Missing 'consolidated_info' key"

    def test_retriever_finds_relevant_documents(self):
        """Verify retriever finds documents for relevant queries."""
        retriever = RagRetriever()
        
        # Test multiple queries
        queries = ["feeding priority", "conflict resolution", "overdue tasks"]
        for query in queries:
            result = retriever.retrieve(query)
            assert result['matched_documents'], f"No documents matched for query: {query}"
            assert len(result['consolidated_info']) > 0, f"No consolidated info for query: {query}"

    def test_retriever_handles_unknown_queries(self):
        """Verify retriever gracefully handles unknown queries."""
        retriever = RagRetriever()
        result = retriever.retrieve("xyzabc nonexistent query 123")

        assert isinstance(result, dict), "Should return dict even for unknown query"
        # May return empty or default message, but shouldn't crash
        assert 'consolidated_info' in result


class TestAiCareCoach:
    """Test the AI Care Coach advice generation."""

    def test_coach_generates_advice_dict(self):
        """Verify coach returns expected advice structure."""
        retriever = RagRetriever()
        coach = AiCareCoach(retriever)

        advice = coach.generate_advice("Feed Buddy", [], [])

        assert isinstance(advice, dict), "Advice should be a dictionary"
        assert 'advice_text' in advice, "Missing 'advice_text' key"
        assert 'retrieval_details' in advice, "Missing 'retrieval_details' key"

    def test_coach_generates_non_empty_advice(self):
        """Verify coach generates actual advice content."""
        retriever = RagRetriever()
        coach = AiCareCoach(retriever)

        advice = coach.generate_advice("Feed Buddy and give medication", [], [])

        assert len(advice['advice_text']) > 0, "Generated advice should not be empty"
        assert len(advice['retrieval_details']) > 0, "Should have retrieval details"

    def test_coach_handles_conflicts(self):
        """Verify coach generates advice when conflicts are detected."""
        retriever = RagRetriever()
        coach = AiCareCoach(retriever)

        conflicts = ["Walk and grooming overlap"]
        advice = coach.generate_advice("Schedule conflict detected", conflicts, [])

        assert len(advice['advice_text']) > 0, "Should generate advice for conflicts"
        # Check that conflict-related retrieval happened
        assert any('conflict' in str(r).lower() for r in advice['retrieval_details']), \
            "Should retrieve conflict resolution info"

    def test_coach_handles_overdue_tasks(self):
        """Verify coach generates advice for overdue tasks."""
        retriever = RagRetriever()
        coach = AiCareCoach(retriever)

        overdue = ["Morning walk"]
        advice = coach.generate_advice("Overdue task", [], overdue)

        assert len(advice['advice_text']) > 0, "Should generate advice for overdue tasks"


class TestEnhancedScheduler:
    """Test the enhanced scheduler with RAG."""

    def test_scheduler_generates_enhanced_summary_dict(self):
        """Verify scheduler returns expected summary structure."""
        owner = Owner('Test Owner')
        pet = Pet('Buddy', 'dog')
        owner.add_pet(pet)

        task = Task('Feed Buddy', datetime.now() + timedelta(hours=1), priority=3)
        pet.add_task(task)

        scheduler = EnhancedScheduler(owner)
        result = scheduler.generate_ai_enhanced_summary()

        assert isinstance(result, dict), "Summary should be a dictionary"
        assert 'summary_text' in result, "Missing 'summary_text'"
        assert 'retrieval_details' in result, "Missing 'retrieval_details'"
        assert 'conflicts' in result, "Missing 'conflicts'"
        assert 'overdue' in result, "Missing 'overdue'"
        assert 'overall_confidence' in result, "Missing 'overall_confidence'"
        assert 'queries_executed' in result, "Missing 'queries_executed'"

    def test_scheduler_includes_ai_advice(self):
        """Verify scheduler includes AI-generated advice in summary."""
        owner = Owner('Test Owner')
        pet = Pet('Buddy', 'dog')
        owner.add_pet(pet)

        task = Task('Feed Buddy', datetime.now() + timedelta(hours=1), priority=3)
        pet.add_task(task)

        scheduler = EnhancedScheduler(owner)
        result = scheduler.generate_ai_enhanced_summary()

        assert 'AI Care Coach' in result['summary_text'], "AI advice should be in summary"
        assert len(result['summary_text']) > 100, "Summary should have substantial content"

    def test_scheduler_detects_conflicts_in_summary(self):
        """Verify scheduler detects and reports conflicts."""
        owner = Owner('Test Owner')
        pet = Pet('Buddy', 'dog')
        owner.add_pet(pet)

        now = datetime.now()
        task1 = Task('Feed Buddy', now + timedelta(hours=1), priority=3, duration=30)
        task2 = Task('Groom Buddy', now + timedelta(hours=1, minutes=15), priority=2, duration=30)
        pet.add_task(task1)
        pet.add_task(task2)

        scheduler = EnhancedScheduler(owner)
        result = scheduler.generate_ai_enhanced_summary()

        assert len(result['conflicts']) > 0, "Should detect overlapping tasks"


class TestRagReliability:
    """Test reliability and consistency of RAG system."""

    def test_retriever_consistency(self):
        """Verify retriever returns consistent results for same query."""
        retriever = RagRetriever()

        result1 = retriever.retrieve("feeding priority")
        result2 = retriever.retrieve("feeding priority")

        assert result1['consolidated_info'] == result2['consolidated_info'], \
            "Same query should return consistent results"

    def test_empty_schedule_generates_fallback(self):
        """Verify system handles empty schedules gracefully."""
        owner = Owner('Test Owner')
        pet = Pet('Buddy', 'dog')
        owner.add_pet(pet)

        scheduler = EnhancedScheduler(owner)
        result = scheduler.generate_ai_enhanced_summary()

        # Should still generate output even with no tasks
        assert len(result['summary_text']) > 0, "Should handle empty schedule"

    def test_advisor_never_crashes(self):
        """Verify advisor handles edge cases without crashing."""
        owner = Owner('Test Owner')
        pet = Pet('Buddy', 'dog')
        owner.add_pet(pet)

        # Add various edge case tasks
        pet.add_task(Task('', datetime.now(), priority=0))  # Empty description
        pet.add_task(Task('Very long task name' * 100, datetime.now()))  # Very long name
        pet.add_task(Task('Special chars !@#$%', datetime.now()))  # Special chars

        scheduler = EnhancedScheduler(owner)
        # Should not crash
        result = scheduler.generate_ai_enhanced_summary()
        assert isinstance(result, dict), "Should handle edge cases gracefully"


class TestConfidenceScoring:
    """Test confidence scoring of RAG outputs."""

    def test_retriever_provides_match_count(self):
        """Verify retriever reports how many documents matched."""
        retriever = RagRetriever()
        result = retriever.retrieve("feeding")

        # Count matched documents as a confidence indicator
        match_count = len(result['matched_documents'])
        assert match_count > 0, "Should report matched documents"

    def test_coach_confidence_based_on_retrieval(self):
        """Verify advice confidence correlates with retrieval success."""
        retriever = RagRetriever()
        coach = AiCareCoach(retriever)

        # Good query - should have high retrieval
        good_advice = coach.generate_advice("Feed and walk pet", [], [])
        good_retrieval_count = len(good_advice['retrieval_details'])

        # Bad query - may have lower retrieval
        bad_advice = coach.generate_advice("xyzabc nonexistent", [], [])
        bad_retrieval_count = len(bad_advice['retrieval_details'])

        # Well-formed query should have at least some retrieval
        assert good_retrieval_count > 0, "Good query should retrieve something"

    def test_scheduler_exposes_confidence_score(self):
        """Verify enhanced scheduler exposes confidence data for evaluation."""
        owner = Owner('Test Owner')
        pet = Pet('Buddy', 'dog')
        owner.add_pet(pet)
        pet.add_task(Task('Feed Buddy', datetime.now() + timedelta(hours=1), priority=3))

        scheduler = EnhancedScheduler(owner)
        result = scheduler.generate_ai_enhanced_summary()

        assert 0.0 <= result['overall_confidence'] <= 1.0
        assert len(result['queries_executed']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
