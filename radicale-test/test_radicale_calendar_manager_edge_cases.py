"""
Edge case tests for RadicaleCalendarManager.
This module contains tests for various edge cases and unusual scenarios.

Test Outline:
1. Multi-day Events
   - Tests creation and retrieval of events spanning multiple days
   - Verifies correct duration calculation

2. All-day Events
   - Tests creation and retrieval of events that last a full day
   - Verifies events can be found when filtering for the specific day

3. Long Text Fields
   - Tests events with extremely long text content (500+ chars in summary, 
     2000+ chars in description, 1000+ chars in location)
   - Verifies text preservation and handling of large content

4. Duplicate Summaries
   - Tests handling of multiple events with identical summaries
   - Verifies events maintain unique IDs and can be distinguished

5. Timezone Handling
   - Tests events with explicit timezone information (UTC)
   - Verifies correct storage and retrieval of timezone-aware events

Event Types Tested:
- Multi-day events (3-day duration)
- All-day events (full 24-hour events)
- Events with extremely long text fields
- Events with duplicate summaries but different times
- Events with explicit timezone information
"""

import time
from datetime import datetime, timedelta, timezone

class RadicaleCalendarManagerEdgeTests:
    """
    Edge case tests for RadicaleCalendarManager.
    This class is designed to be used by the main test suite.
    """
    
    def __init__(self, test_case):
        """
        Initialize with a reference to the parent test case.
        
        Args:
            test_case: The parent TestCase instance
        """
        self.test_case = test_case
        
    def run_all_edge_tests(self):
        """Run all edge case tests."""
        self.test_multiday_events()
        self.test_all_day_events()
        self.test_long_text_fields()
        self.test_duplicate_summaries()
        self.test_timezone_handling()
    
    def test_multiday_events(self):
        """Test creating and retrieving events that span multiple days."""
        now = datetime.now().replace(microsecond=0)
        
        # Create a 3-day event
        test_summary = f"Multi-day {self.test_case.generate_unique_summary()}"
        multi_day_event = {
            "summary": test_summary,
            "start": now.isoformat(),
            "end": (now + timedelta(days=3)).isoformat(),
            "description": "This event spans multiple days"
        }
        
        # Add the event
        event_id = self.test_case.manager.add_event(
            self.test_case.test_calendar, 
            multi_day_event
        )
        self.test_case.assertIsNotNone(event_id, "Failed to create multi-day event")
        self.test_case.__class__.events_to_cleanup.append(event_id)
        
        # Wait for the server to process
        time.sleep(1)
        
        # Retrieve the event
        events = self.test_case.manager.get_events(
            self.test_case.test_calendar,
            now,
            now + timedelta(days=4)
        )
        
        found_event = None
        for event in events:
            if event.get("summary") == test_summary:
                found_event = event
                break
                
        self.test_case.assertIsNotNone(found_event, "Multi-day event not found after creation")
        
        # Verify it spans multiple days
        if found_event:
            start = datetime.fromisoformat(found_event.get("start").replace("Z", "+00:00"))
            end = datetime.fromisoformat(found_event.get("end").replace("Z", "+00:00"))
            duration = end - start
            self.test_case.assertTrue(duration.days >= 2, 
                           f"Event duration should be at least 2 days, got {duration}")
    
    def test_all_day_events(self):
        """Test creating and retrieving all-day events."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Create an all-day event
        test_summary = f"All-day {self.test_case.generate_unique_summary()}"
        all_day_event = {
            "summary": test_summary,
            "start": today.isoformat(),
            "end": (today + timedelta(days=1) - timedelta(seconds=1)).isoformat(),
            "description": "This is an all-day event"
        }
        
        # Add the event
        event_id = self.test_case.manager.add_event(
            self.test_case.test_calendar, 
            all_day_event
        )
        self.test_case.assertIsNotNone(event_id, "Failed to create all-day event")
        self.test_case.__class__.events_to_cleanup.append(event_id)
        
        # Wait for the server to process
        time.sleep(1)
        
        # Retrieve the event - just for today
        events = self.test_case.manager.get_events(
            self.test_case.test_calendar,
            today,
            today + timedelta(days=1) - timedelta(seconds=1)
        )
        
        found_event = None
        for event in events:
            if event.get("summary") == test_summary:
                found_event = event
                break
                
        self.test_case.assertIsNotNone(found_event, "All-day event not found when filtering for today only")
    
    def test_long_text_fields(self):
        """Test handling of events with very long text fields."""
        now = datetime.now().replace(microsecond=0)
        
        # Create an event with long text in various fields
        test_summary = f"Long text {self.test_case.generate_unique_summary()}"
        long_summary = test_summary + " " + "x" * 500  # Add 500 x's to the summary
        long_description = "Description: " + "y" * 2000  # 2000 character description
        long_location = "Location: " + "z" * 1000  # 1000 character location
        
        long_text_event = {
            "summary": long_summary,
            "start": now.isoformat(),
            "end": (now + timedelta(hours=1)).isoformat(),
            "description": long_description,
            "location": long_location
        }
        
        # Add the event
        event_id = self.test_case.manager.add_event(
            self.test_case.test_calendar, 
            long_text_event
        )
        self.test_case.assertIsNotNone(event_id, "Failed to create event with long text fields")
        self.test_case.__class__.events_to_cleanup.append(event_id)
        
        # Wait for the server to process
        time.sleep(1)
        
        # Retrieve the event
        events = self.test_case.manager.get_events(
            self.test_case.test_calendar,
            now,
            now + timedelta(hours=2)
        )
        
        found_event = None
        for event in events:
            # Look for the event using a substring match (in case the text was truncated)
            if test_summary in event.get("summary", ""):
                found_event = event
                break
                
        self.test_case.assertIsNotNone(found_event, "Event with long text fields not found")
        
        # Check if the text was preserved (or at least partially preserved)
        if found_event:
            # Some servers might truncate long fields, so we check if at least some of the text is there
            self.test_case.assertTrue(len(found_event.get("summary", "")) > 50, 
                            "Summary was severely truncated")
            self.test_case.assertTrue(len(found_event.get("description", "")) > 50, 
                            "Description was severely truncated")
            self.test_case.assertTrue(len(found_event.get("location", "")) > 50, 
                            "Location was severely truncated")
    
    def test_duplicate_summaries(self):
        """Test handling of events with identical summaries."""
        now = datetime.now().replace(microsecond=0)
        
        # Create a unique but identifiable summary
        duplicate_summary = f"Duplicate {self.test_case.generate_unique_summary()}"
        
        # Create first event
        event1_data = {
            "summary": duplicate_summary,
            "start": now.isoformat(),
            "end": (now + timedelta(hours=1)).isoformat(),
            "description": "First event with duplicate summary"
        }
        
        # Create second event with same summary but different time
        event2_data = {
            "summary": duplicate_summary,
            "start": (now + timedelta(hours=2)).isoformat(),
            "end": (now + timedelta(hours=3)).isoformat(),
            "description": "Second event with duplicate summary"
        }
        
        # Add both events
        event1_id = self.test_case.manager.add_event(
            self.test_case.test_calendar, 
            event1_data
        )
        self.test_case.assertIsNotNone(event1_id, "Failed to create first duplicate summary event")
        self.test_case.__class__.events_to_cleanup.append(event1_id)
        
        event2_id = self.test_case.manager.add_event(
            self.test_case.test_calendar, 
            event2_data
        )
        self.test_case.assertIsNotNone(event2_id, "Failed to create second duplicate summary event")
        self.test_case.__class__.events_to_cleanup.append(event2_id)
        
        # Wait for the server to process
        time.sleep(1)
        
        # Retrieve both events
        events = self.test_case.manager.get_events(
            self.test_case.test_calendar,
            now,
            now + timedelta(hours=4)
        )
        
        # Find events with our duplicate summary
        duplicate_events = []
        for event in events:
            if event.get("summary") == duplicate_summary:
                duplicate_events.append(event)
        
        # Verify we can find both events
        self.test_case.assertEqual(len(duplicate_events), 2, 
                        f"Expected 2 events with duplicate summary, found {len(duplicate_events)}")
        
        # Verify the events have different IDs
        self.test_case.assertNotEqual(duplicate_events[0].get("id"), duplicate_events[1].get("id"),
                        "Events with same summary should have different IDs")
    
    def test_timezone_handling(self):
        """Test handling of events with explicit timezone information."""

        # Then use it in the method:
        now_utc = datetime.now(tz=timezone.utc).replace(microsecond=0)

        test_summary = f"Timezone {self.test_case.generate_unique_summary()}"
        timezone_event = {
            "summary": test_summary,
            "start": now_utc.isoformat(),
            "end": (now_utc + timedelta(hours=1)).isoformat(),
            "description": "Event with explicit timezone"
        }
        
        # Add the event
        event_id = self.test_case.manager.add_event(
            self.test_case.test_calendar, 
            timezone_event
        )
        self.test_case.assertIsNotNone(event_id, "Failed to create event with timezone")
        self.test_case.__class__.events_to_cleanup.append(event_id)
        
        # Wait for the server to process
        time.sleep(1)
        
        # Retrieve the event
        events = self.test_case.manager.get_events(
            self.test_case.test_calendar,
            now_utc - timedelta(hours=1),
            now_utc + timedelta(hours=2)
        )
        
        found_event = None
        for event in events:
            if event.get("summary") == test_summary:
                found_event = event
                break
                
        self.test_case.assertIsNotNone(found_event, "Event with timezone not found")
