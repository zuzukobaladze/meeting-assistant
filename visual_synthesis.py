import openai
import json
import os
import base64
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

class VisualSynthesisEngine:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "dall-e-3"
        self.image_quality = "standard"  # or "hd" for higher quality
        self.image_size = "1024x1024"   # DALL-E 3 supports 1024x1024, 1792x1024, 1024x1792
        
    def generate_meeting_visual_summary(self, meeting_title: str, summary: str, 
                                      key_points: List[str], style: str = "professional") -> Dict:
        """Generate a visual summary of the meeting using DALL-E 3"""
        
        # Create a focused prompt for meeting visualization
        prompt = self._create_summary_prompt(meeting_title, summary, key_points, style)
        
        try:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=self.image_size,
                quality=self.image_quality,
                n=1
            )
            
            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt
            
            return {
                'success': True,
                'image_url': image_url,
                'prompt_used': prompt,
                'revised_prompt': revised_prompt,
                'image_type': 'meeting_summary',
                'style': style
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'prompt_used': prompt,
                'image_type': 'meeting_summary'
            }
    
    def generate_action_items_visual(self, action_items: List[Dict], 
                                   meeting_title: str, style: str = "infographic") -> Dict:
        """Generate a visual representation of action items"""
        
        if not action_items:
            return {'success': False, 'error': 'No action items to visualize'}
        
        prompt = self._create_action_items_prompt(action_items, meeting_title, style)
        
        try:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size="1792x1024",  # Wider format for action items layout
                quality=self.image_quality,
                n=1
            )
            
            return {
                'success': True,
                'image_url': response.data[0].url,
                'prompt_used': prompt,
                'revised_prompt': response.data[0].revised_prompt,
                'image_type': 'action_items',
                'style': style
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'prompt_used': prompt,
                'image_type': 'action_items'
            }
    
    def generate_decisions_visual(self, decisions: List[Dict], 
                                meeting_title: str, style: str = "flowchart") -> Dict:
        """Generate a visual representation of key decisions"""
        
        if not decisions:
            return {'success': False, 'error': 'No decisions to visualize'}
        
        prompt = self._create_decisions_prompt(decisions, meeting_title, style)
        
        try:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=self.image_size,
                quality=self.image_quality,
                n=1
            )
            
            return {
                'success': True,
                'image_url': response.data[0].url,
                'prompt_used': prompt,
                'revised_prompt': response.data[0].revised_prompt,
                'image_type': 'decisions',
                'style': style
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'prompt_used': prompt,
                'image_type': 'decisions'
            }
    
    def generate_presentation_slide(self, slide_content: Dict, 
                                  template_style: str = "corporate") -> Dict:
        """Generate a presentation slide for the meeting content"""
        
        prompt = self._create_slide_prompt(slide_content, template_style)
        
        try:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size="1792x1024",  # Presentation aspect ratio
                quality=self.image_quality,
                n=1
            )
            
            return {
                'success': True,
                'image_url': response.data[0].url,
                'prompt_used': prompt,
                'revised_prompt': response.data[0].revised_prompt,
                'image_type': 'presentation_slide',
                'style': template_style
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'prompt_used': prompt,
                'image_type': 'presentation_slide'
            }
    
    def generate_meeting_infographic(self, meeting_data: Dict, 
                                   infographic_type: str = "overview") -> Dict:
        """Generate an infographic summarizing the meeting"""
        
        prompt = self._create_infographic_prompt(meeting_data, infographic_type)
        
        try:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size="1024x1792",  # Vertical infographic format
                quality=self.image_quality,
                n=1
            )
            
            return {
                'success': True,
                'image_url': response.data[0].url,
                'prompt_used': prompt,
                'revised_prompt': response.data[0].revised_prompt,
                'image_type': 'infographic',
                'style': infographic_type
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'prompt_used': prompt,
                'image_type': 'infographic'
            }
    
    def create_visual_presentation_pack(self, meeting_id: int, meeting_data: Dict) -> List[Dict]:
        """Generate a complete set of visual assets for presentation"""
        
        visual_pack = []
        
        # 1. Meeting Summary Visual
        if meeting_data.get('summary'):
            key_points = []
            if meeting_data.get('key_topics'):
                key_points = [topic.get('topic', topic) if isinstance(topic, dict) else str(topic) 
                             for topic in meeting_data['key_topics'][:5]]
            
            summary_visual = self.generate_meeting_visual_summary(
                meeting_data.get('title', 'Meeting'),
                meeting_data['summary'],
                key_points,
                style="professional"
            )
            if summary_visual['success']:
                visual_pack.append({
                    'type': 'summary',
                    'title': 'Meeting Overview',
                    'visual': summary_visual
                })
        
        # 2. Action Items Visual
        if meeting_data.get('action_items'):
            action_visual = self.generate_action_items_visual(
                meeting_data['action_items'],
                meeting_data.get('title', 'Meeting'),
                style="infographic"
            )
            if action_visual['success']:
                visual_pack.append({
                    'type': 'action_items',
                    'title': 'Action Items & Next Steps',
                    'visual': action_visual
                })
        
        # 3. Decisions Visual
        if meeting_data.get('decisions'):
            decisions_visual = self.generate_decisions_visual(
                meeting_data['decisions'],
                meeting_data.get('title', 'Meeting'),
                style="flowchart"
            )
            if decisions_visual['success']:
                visual_pack.append({
                    'type': 'decisions',
                    'title': 'Key Decisions Made',
                    'visual': decisions_visual
                })
        
        # 4. Meeting Infographic
        infographic = self.generate_meeting_infographic(
            meeting_data,
            infographic_type="comprehensive"
        )
        if infographic['success']:
            visual_pack.append({
                'type': 'infographic',
                'title': 'Meeting Infographic',
                'visual': infographic
            })
        
        return visual_pack
    
    def _create_summary_prompt(self, title: str, summary: str, key_points: List[str], style: str) -> str:
        """Create a DALL-E prompt for meeting summary visualization"""
        
        # Limit summary length for prompt
        summary_snippet = summary[:300] + "..." if len(summary) > 300 else summary
        
        # Format key points
        points_text = ""
        if key_points:
            points_text = f" Key topics include: {', '.join(key_points[:4])}"
        
        style_descriptors = {
            "professional": "clean, modern, corporate design with blue and white colors, minimalist layout",
            "creative": "colorful, engaging design with modern typography and creative elements",
            "technical": "structured, diagram-style with charts and technical elements",
            "infographic": "infographic style with icons, charts, and visual hierarchy"
        }
        
        style_desc = style_descriptors.get(style, style_descriptors["professional"])
        
        prompt = f"""Create a {style_desc} visual summary for a business meeting titled '{title}'. 
        The meeting covered: {summary_snippet}{points_text}
        
        Design requirements:
        - Professional business presentation style
        - Clear readable text with meeting title prominently displayed
        - Visual elements representing the meeting content
        - Clean layout suitable for sharing with stakeholders
        - No people or faces, focus on concepts and information
        - Use abstract shapes, icons, or diagrams to represent ideas
        - Corporate color scheme appropriate for business use"""
        
        return prompt
    
    def _create_action_items_prompt(self, action_items: List[Dict], title: str, style: str) -> str:
        """Create a DALL-E prompt for action items visualization"""
        
        # Extract action items text
        actions_text = []
        for item in action_items[:5]:  # Limit to top 5 items
            if isinstance(item, dict):
                action_desc = item.get('item', item.get('description', 'Action item'))
                owner = item.get('owner', item.get('assigned_to', ''))
                priority = item.get('priority', '')
                
                action_text = f"{action_desc}"
                if owner:
                    action_text += f" (Owner: {owner})"
                if priority:
                    action_text += f" [Priority: {priority}]"
            else:
                action_text = str(item)
            
            actions_text.append(action_text)
        
        actions_summary = "; ".join(actions_text)[:400]  # Limit length
        
        prompt = f"""Create a professional business infographic showing action items from the meeting '{title}'.
        
        Action items to visualize: {actions_summary}
        
        Design requirements:
        - Horizontal layout (landscape orientation) suitable for presentations
        - Clear task checklist or action board style
        - Use icons like checkboxes, arrows, or task symbols
        - Professional color scheme (blues, greens, corporate colors)
        - Clear typography for readability
        - Visual hierarchy showing priorities if mentioned
        - No people or faces, focus on task visualization
        - Include elements like calendars, clocks, or progress indicators
        - Modern, clean business presentation style"""
        
        return prompt
    
    def _create_decisions_prompt(self, decisions: List[Dict], title: str, style: str) -> str:
        """Create a DALL-E prompt for decisions visualization"""
        
        # Extract decision text
        decisions_text = []
        for decision in decisions[:4]:  # Limit to top 4 decisions
            if isinstance(decision, dict):
                decision_desc = decision.get('decision', decision.get('description', 'Decision made'))
                context = decision.get('context', decision.get('reason', ''))
                
                decision_text = decision_desc
                if context:
                    decision_text += f" (Context: {context[:100]})"
            else:
                decision_text = str(decision)
            
            decisions_text.append(decision_text)
        
        decisions_summary = "; ".join(decisions_text)[:400]  # Limit length
        
        prompt = f"""Create a professional business flowchart or decision tree visualization for meeting '{title}'.
        
        Key decisions made: {decisions_summary}
        
        Design requirements:
        - Clean flowchart or decision tree layout
        - Professional business style with corporate colors
        - Use decision diamond shapes, arrows, and boxes
        - Clear visual flow showing decision processes
        - Modern typography for easy reading
        - No people or faces, focus on decision concepts
        - Include elements like arrows, checkmarks, or process symbols
        - Suitable for business presentations and stakeholder sharing
        - Abstract visual representation of decision outcomes"""
        
        return prompt
    
    def _create_slide_prompt(self, slide_content: Dict, template_style: str) -> str:
        """Create a DALL-E prompt for presentation slide"""
        
        slide_title = slide_content.get('title', 'Meeting Summary')
        content = slide_content.get('content', '')[:300]  # Limit content
        slide_type = slide_content.get('type', 'summary')
        
        style_descriptors = {
            "corporate": "clean corporate presentation template with professional blue and white colors",
            "modern": "modern sleek design with gradients and contemporary typography",
            "minimal": "minimalist design with lots of white space and simple elements",
            "creative": "creative presentation design with engaging visual elements"
        }
        
        style_desc = style_descriptors.get(template_style, style_descriptors["corporate"])
        
        prompt = f"""Create a {style_desc} presentation slide template.
        
        Slide title: '{slide_title}'
        Content to represent: {content}
        
        Design requirements:
        - Horizontal presentation slide layout (16:10 or 16:9 aspect ratio)
        - Professional business presentation style
        - Clear title area at the top
        - Content area with visual elements representing the information
        - No actual readable text content - focus on layout and visual design
        - Use placeholder text areas and visual elements
        - Corporate color scheme suitable for business presentations
        - Clean, modern typography placeholders
        - Professional layout suitable for stakeholder presentations
        - Abstract visual elements that complement the content theme"""
        
        return prompt
    
    def _create_infographic_prompt(self, meeting_data: Dict, infographic_type: str) -> str:
        """Create a DALL-E prompt for meeting infographic"""
        
        title = meeting_data.get('title', 'Meeting')
        summary = meeting_data.get('summary', '')[:200]
        
        # Count elements
        action_count = len(meeting_data.get('action_items', []))
        decision_count = len(meeting_data.get('decisions', []))
        topic_count = len(meeting_data.get('key_topics', []))
        
        stats_text = f"Meeting included {action_count} action items, {decision_count} decisions, and {topic_count} key topics discussed"
        
        prompt = f"""Create a comprehensive business meeting infographic for '{title}'.
        
        Meeting summary: {summary}
        Statistics: {stats_text}
        
        Design requirements:
        - Vertical infographic layout (portrait orientation)
        - Professional business infographic style
        - Include visual statistics with numbers and charts
        - Use icons for different meeting elements (actions, decisions, topics)
        - Corporate color scheme (blues, greens, professional colors)
        - Clear visual hierarchy with sections
        - Charts, graphs, or visual data representations
        - Modern, clean design suitable for sharing
        - No people or faces, focus on data visualization
        - Include timeline elements, statistics, and key metrics
        - Professional typography and layout
        - Suitable for executive summaries and stakeholder reports"""
        
        return prompt
    
    def download_and_save_image(self, image_url: str, filename: str, save_directory: str = "visuals") -> Optional[str]:
        """Download image from URL and save locally"""
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(save_directory, exist_ok=True)
            
            # Download image
            response = requests.get(image_url)
            response.raise_for_status()
            
            # Save to file
            file_path = os.path.join(save_directory, filename)
            with open(file_path, 'wb') as file:
                file.write(response.content)
            
            return file_path
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def get_image_as_base64(self, image_url: str) -> Optional[str]:
        """Get image as base64 encoded string for embedding"""
        
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            
            # Convert to base64
            base64_image = base64.b64encode(response.content).decode('utf-8')
            return base64_image
            
        except Exception as e:
            print(f"Error converting image to base64: {e}")
            return None 