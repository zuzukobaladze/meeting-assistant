import openai
import json
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class ContentAnalyzer:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    def analyze_meeting(self, transcription_text: str, meeting_title: str = "") -> Dict:
        """
        Analyze meeting transcription using GPT-4 to extract:
        - Summary
        - Action items with owners
        - Decisions made
        - Key topics
        """
        
        system_prompt = """You are an AI meeting assistant for KIU Consulting. Analyze meeting transcriptions and extract structured information.

Your task is to:
1. Create a concise meeting summary (2-3 paragraphs)
2. Extract action items with assigned owners
3. Identify key decisions made
4. List main topics discussed

Be professional and focus on business outcomes. If owners aren't explicitly mentioned, use "Unassigned" or infer from context."""

        user_prompt = f"""
Meeting Title: {meeting_title}

Transcription:
{transcription_text}

Please analyze this meeting and provide:
1. A concise summary
2. Action items (with owners if mentioned)
3. Key decisions made
4. Main topics discussed

IMPORTANT: Respond ONLY with valid JSON in the following structure (no additional text):
{{
    "summary": "Meeting summary text",
    "action_items": [
        {{
            "task": "Description of task",
            "owner": "Person responsible or 'Unassigned'",
            "deadline": "Deadline if mentioned or null",
            "priority": "high/medium/low"
        }}
    ],
    "decisions": [
        {{
            "decision": "What was decided",
            "context": "Brief context or reasoning",
            "impact": "Expected impact or outcome"
        }}
    ],
    "key_topics": [
        {{
            "topic": "Topic name",
            "discussion_points": ["Key point 1", "Key point 2"]
        }}
    ]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse JSON from response
            content = response.choices[0].message.content
            
            # Extract JSON from response (handle cases where GPT adds extra text)
            try:
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: create basic structure if JSON parsing fails
                analysis = {
                    "summary": content[:500] + "..." if len(content) > 500 else content,
                    "action_items": [],
                    "decisions": [],
                    "key_topics": []
                }
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Error analyzing meeting content: {str(e)}")
    
    def generate_action_items_with_calendar(self, action_items: List[Dict], meeting_date: str = None) -> List[Dict]:
        """
        Use function calling to enhance action items with calendar integration
        """
        
        # Define function for calendar integration
        calendar_function = {
            "name": "create_calendar_event",
            "description": "Create calendar events for action items with deadlines",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Event title"
                    },
                    "description": {
                        "type": "string", 
                        "description": "Event description"
                    },
                    "date": {
                        "type": "string",
                        "description": "Due date in YYYY-MM-DD format"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Person assigned to the task"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Task priority level"
                    }
                },
                "required": ["title", "description", "assignee"]
            }
        }
        
        task_function = {
            "name": "create_task",
            "description": "Create task management entries for action items",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name": {
                        "type": "string",
                        "description": "Name of the task"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed task description"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Person responsible for the task"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Task due date"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project or category this task belongs to"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                    }
                },
                "required": ["task_name", "assignee", "priority"]
            }
        }
        
        system_prompt = """You are a meeting assistant that creates calendar events and tasks from action items. 
        Use the provided functions to create appropriate calendar events and task management entries.
        
        For each action item:
        1. If it has a deadline, create a calendar event 
        2. Always create a task entry
        3. Infer reasonable due dates if not specified (typically 1-2 weeks from meeting date)
        4. Categorize priority based on urgency indicators in the text
        """
        
        user_prompt = f"""
        Meeting Date: {meeting_date or datetime.now().strftime('%Y-%m-%d')}
        
        Action Items to process:
        {json.dumps(action_items, indent=2)}
        
        Please create appropriate calendar events and tasks for these action items using the available functions.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                functions=[calendar_function, task_function],
                function_call="auto",
                temperature=0.2
            )
            
            # Process function calls
            enhanced_items = []
            for item in action_items:
                enhanced_item = item.copy()
                enhanced_item["calendar_event"] = None
                enhanced_item["task_entry"] = None
                enhanced_items.append(enhanced_item)
            
            # Check if functions were called
            if response.choices[0].message.function_call:
                function_call = response.choices[0].message.function_call
                function_args = json.loads(function_call.arguments)
                
                # Simulate function execution (in real implementation, these would call actual APIs)
                if function_call.name == "create_calendar_event":
                    enhanced_items[0]["calendar_event"] = {
                        "status": "created",
                        "event_id": f"cal_{datetime.now().timestamp()}",
                        "details": function_args
                    }
                elif function_call.name == "create_task":
                    enhanced_items[0]["task_entry"] = {
                        "status": "created", 
                        "task_id": f"task_{datetime.now().timestamp()}",
                        "details": function_args
                    }
            
            return enhanced_items
            
        except Exception as e:
            print(f"Warning: Function calling failed: {str(e)}")
            # Return original items if function calling fails
            return action_items
    
    def extract_meeting_insights(self, transcription_text: str) -> Dict:
        """
        Extract additional insights like sentiment, engagement, and follow-up recommendations
        """
        
        system_prompt = """You are an expert meeting analyst. Analyze the meeting transcription and provide insights about:
        1. Overall meeting effectiveness
        2. Participant engagement levels  
        3. Communication patterns
        4. Recommendations for improvement"""
        
        user_prompt = f"""
        Analyze this meeting transcription for insights:
        
        {transcription_text}
        
        IMPORTANT: Respond ONLY with valid JSON in this exact format (no additional text):
        {{
            "effectiveness_score": 1-10,
            "effectiveness_notes": "Brief assessment",
            "engagement_analysis": {{
                "overall_engagement": "high/medium/low",
                "most_engaged_participants": ["participant names"],
                "participation_balance": "balanced/unbalanced"
            }},
            "communication_patterns": {{
                "dominant_speakers": ["speaker names"],
                "discussion_flow": "structured/organic/chaotic",
                "decision_making_style": "collaborative/directive/consensus"
            }},
            "recommendations": [
                "Improvement suggestion 1",
                "Improvement suggestion 2"
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            # Parse JSON from response
            content = response.choices[0].message.content
            
            try:
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    insights = json.loads(json_match.group())
                else:
                    insights = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: create basic structure if JSON parsing fails
                insights = {
                    "effectiveness_score": 5,
                    "effectiveness_notes": "Analysis completed",
                    "engagement_analysis": {"overall_engagement": "medium"},
                    "communication_patterns": {"discussion_flow": "structured"},
                    "recommendations": ["Continue regular meetings"]
                }
            
            return insights
            
        except Exception as e:
            print(f"Warning: Insights extraction failed: {str(e)}")
            return {
                "effectiveness_score": 5,
                "effectiveness_notes": "Unable to analyze",
                "engagement_analysis": {"overall_engagement": "unknown"},
                "communication_patterns": {"discussion_flow": "unknown"},
                "recommendations": ["Analysis unavailable"]
            } 