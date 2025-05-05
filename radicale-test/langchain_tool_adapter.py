"""
LangChain Tool Adapter for Radicale Calendar Manager

This module provides a LangChain Tool adapter for the RadicaleCalendarManager class,
allowing calendar operations to be used as LangChain tools.

Components:
1. CalendarToolAdapter
   - Wraps RadicaleCalendarManager functionality into LangChain tools
   - Provides tools for listing, adding, updating and deleting calendar events
   - Handles date/time conversions between string and datetime objects

Tools Provided:
- list_calendar_events: List events from a calendar within a date range
- add_calendar_event: Add a new event to a calendar
- update_calendar_event: Update an existing calendar event  
- delete_calendar_event: Delete an event from a calendar
- list_available_calendars: List all available calendars

Usage:
    adapter = CalendarToolAdapter(url="...", username="...", password="...")
    tools = adapter.get_all_tools()
    # Use tools with LangChain
"""

from langchain_core.tools import Tool, StructuredTool
from typing import Optional, List, Dict, Any
from datetime import datetime

from radicale_calendar_manager import RadicaleCalendarManager  # Import your class

class CalendarToolAdapter:
    """Adapter to provide LangChain Tools for calendar operations"""
    
    def __init__(self, url: str, username: str, password: str):
        """Initialize with RadicaleCalendarManager credentials"""
        self.manager = RadicaleCalendarManager(url=url, username=username, password=password)
        # TODO: Consider adding error handling for connection failures
        self.manager.connect()
        
    def get_all_tools(self) -> List[Tool]:
        """Return all calendar tools"""
        tools = [
            StructuredTool.from_function(
                func=self.list_events,
                name="list_calendar_events",
                description="List events from a calendar within a date range"
            ),
            StructuredTool.from_function(
                func=self.add_event,
                name="add_calendar_event",
                description="Add a new event to a calendar"
            ),
            StructuredTool.from_function(
                func=self.update_event,
                name="update_calendar_event",
                description="Update an existing calendar event"
            ),
            StructuredTool.from_function(
                func=self.delete_event,
                name="delete_calendar_event",
                description="Delete an event from a calendar"
            ),
            StructuredTool.from_function(
                func=self.list_calendars,
                name="list_available_calendars",
                description="List all available calendars"
            )
        ]
        return tools
    
    def list_calendars(self) -> List[str]:
        """List all available calendars"""
        # TODO: Add error handling if calendars property is not available
        return [calendar.name for calendar in self.manager.calendars]
    
    def list_events(self, 
                   calendar_name: Optional[str] = None, 
                   start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List events from a calendar within a date range.
        
        Args:
            calendar_name: Name of the calendar to fetch events from
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            List of event dictionaries
        """
        # Parse date strings to datetime objects if provided
        start_datetime = None
        end_datetime = None
        
        # TODO: Add try/except blocks to handle invalid date formats
        if start_date:
            start_datetime = datetime.fromisoformat(start_date)
        if end_date:
            end_datetime = datetime.fromisoformat(end_date)
            
        # TODO: Consider adding validation for calendar_name
        return self.manager.get_events(
            calendar_name=calendar_name,
            start_date=start_datetime,
            end_date=end_datetime
        )
    
    def add_event(self, 
                 calendar_name: str, 
                 summary: str, 
                 start: str, 
                 end: Optional[str] = None,
                 location: Optional[str] = None,
                 description: Optional[str] = None) -> str:
        """
        Add a new event to a calendar.
        
        Args:
            calendar_name: Name of the calendar
            summary: Event title/summary
            start: Start datetime in ISO format (YYYY-MM-DDTHH:MM:SS)
            end: End datetime in ISO format (YYYY-MM-DDTHH:MM:SS)
            location: Event location
            description: Event description
            
        Returns:
            Event ID of the created event
        """
        # TODO: Add validation for required fields and date format
        event_data = {
            "summary": summary,
            "start": start
        }
        
        if end:
            event_data["end"] = end
        if location:
            event_data["location"] = location
        if description:
            event_data["description"] = description
            
        # TODO: Add error handling for failed event creation
        return self.manager.add_event(calendar_name, event_data)
    
    def update_event(self,
                    calendar_name: str,
                    event_id: str,
                    summary: Optional[str] = None,
                    start: Optional[str] = None,
                    end: Optional[str] = None,
                    location: Optional[str] = None,
                    description: Optional[str] = None) -> bool:
        """
        Update an existing calendar event.
        
        Args:
            calendar_name: Name of the calendar
            event_id: ID of the event to update
            summary: New event title/summary
            start: New start datetime in ISO format
            end: New end datetime in ISO format
            location: New event location
            description: New event description
            
        Returns:
            True if update was successful
        """
        # TODO: Add validation to ensure at least one field is being updated
        event_data = {}
        
        if summary:
            event_data["summary"] = summary
        if start:
            # TODO: Add validation for date format
            event_data["start"] = start
        if end:
            # TODO: Add validation for date format
            event_data["end"] = end
        if location:
            event_data["location"] = location
        if description:
            event_data["description"] = description
            
        # TODO: Add error handling for non-existent events
        return self.manager.set_event(calendar_name, event_id, event_data)
    
    def delete_event(self, calendar_name: str, event_id: str) -> bool:
        """
        Delete an event from a calendar.
        
        Args:
            calendar_name: Name of the calendar
            event_id: ID of the event to delete
            
        Returns:
            True if deletion was successful
        """
        # TODO: Add validation for calendar_name and event_id
        # TODO: Add error handling for non-existent events
        return self.manager.delete_event(calendar_name, event_id)
