"""Unit tests for daily quota tracking."""

from ace.llm.quota import QuotaTracker

def test_quota_reservation_and_limit(temp_db):
    tracker = QuotaTracker(db_path=temp_db)
    
    # Check initial reservation
    allowed = tracker.check_and_reserve(provider="gemini-flash", api_key_id=0, limit_requests=2)
    assert allowed is True
    
    # Record first usage
    tracker.record_usage(provider="gemini-flash", api_key_id=0, tokens_used=100)
    allowed = tracker.check_and_reserve(provider="gemini-flash", api_key_id=0, limit_requests=2)
    assert allowed is True
    
    # Record second usage (at limit)
    tracker.record_usage(provider="gemini-flash", api_key_id=0, tokens_used=100)
    allowed = tracker.check_and_reserve(provider="gemini-flash", api_key_id=0, limit_requests=2)
    assert allowed is False  # Limit reached
