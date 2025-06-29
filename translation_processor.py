import openai
import json
from typing import Dict, List, Optional

class TranslationProcessor:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
        # Supported low resource languages
        self.supported_languages = {
            'georgian': {
                'name': 'Georgian',
                'code': 'ka',
                'native_name': 'ქართული'
            },
            'slovak': {
                'name': 'Slovak', 
                'code': 'sk',
                'native_name': 'Slovenčina'
            },
            'slovenian': {
                'name': 'Slovenian',
                'code': 'sl', 
                'native_name': 'Slovenščina'
            },
            'latvian': {
                'name': 'Latvian',
                'code': 'lv',
                'native_name': 'Latviešu'
            },
            'lithuanian': {
                'name': 'Lithuanian',
                'code': 'lt',
                'native_name': 'Lietuvių'
            },
            'estonian': {
                'name': 'Estonian',
                'code': 'et',
                'native_name': 'Eesti'
            },
            'bulgarian': {
                'name': 'Bulgarian',
                'code': 'bg',
                'native_name': 'Български'
            },
            'croatian': {
                'name': 'Croatian',
                'code': 'hr',
                'native_name': 'Hrvatski'
            },
            'albanian': {
                'name': 'Albanian',
                'code': 'sq',
                'native_name': 'Shqip'
            },
            'macedonian': {
                'name': 'Macedonian',
                'code': 'mk',
                'native_name': 'Македонски'
            }
        }
    
    def get_supported_languages(self) -> Dict:
        """Get list of supported languages"""
        return self.supported_languages
    
    def translate_text(self, text: str, target_language: str, content_type: str = "general") -> Dict:
        """
        Translate text to target language using GPT-4
        
        Args:
            text: Text to translate
            target_language: Language key from supported_languages
            content_type: Type of content (transcript, summary, action_items, etc.)
        
        Returns:
            Dict containing translated text and metadata
        """
        
        if target_language not in self.supported_languages:
            raise ValueError(f"Unsupported language: {target_language}")
        
        lang_info = self.supported_languages[target_language]
        
        # Create context-aware system prompt
        system_prompt = f"""You are a professional translator specializing in business and meeting content. 
        
        Translate the following text into {lang_info['name']} ({lang_info['native_name']}). 

        Guidelines:
        - Maintain professional business tone
        - Preserve technical terms and proper names appropriately
        - Keep formatting and structure intact
        - For meeting content, preserve speaker attributions and timestamps
        - Ensure cultural appropriateness for business context
        - If translating action items or decisions, maintain clarity and actionability
        
        Respond ONLY with the translated text, no additional commentary."""
        
        # Customize prompt based on content type
        if content_type == "transcript":
            system_prompt += "\n\nThis is a meeting transcript. Preserve speaker labels and maintain conversation flow."
        elif content_type == "summary":
            system_prompt += "\n\nThis is a meeting summary. Maintain executive summary style and key business points."
        elif content_type == "action_items":
            system_prompt += "\n\nThese are action items. Keep them clear, actionable, and preserve ownership assignments."
        elif content_type == "decisions":
            system_prompt += "\n\nThese are meeting decisions. Maintain clarity of what was decided and business implications."
        
        try:
            # Add text length check and truncation for very long content
            max_chars = 8000  # Reasonable limit for GPT-4
            if len(text) > max_chars:
                print(f"⚠️  Text too long ({len(text)} chars), truncating to {max_chars} chars")
                text = text[:max_chars] + "... [Content truncated for translation]"
            
            print(f"🔄 Translating {content_type} to {lang_info['name']} ({len(text)} chars)...")
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,  # Low temperature for consistent translations
                max_tokens=4000,

            )
            
            translated_text = response.choices[0].message.content.strip()
            print(f"✅ Translation completed for {content_type}")
            
            return {
                'translated_text': translated_text,
                'target_language': target_language,
                'language_name': lang_info['name'],
                'language_code': lang_info['code'],
                'native_name': lang_info['native_name'],
                'content_type': content_type,
                'original_length': len(text),
                'translated_length': len(translated_text)
            }
            
        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")
    
    def translate_meeting_content(self, meeting_data: Dict, target_language: str) -> Dict:
        """
        Translate complete meeting content including transcript, summary, action items, etc.
        
        Args:
            meeting_data: Dictionary containing meeting content
            target_language: Target language key
            
        Returns:
            Dictionary with all translated content
        """
        
        translations = {}
        lang_info = self.supported_languages[target_language]
        
        try:
            print(f"🌐 Starting translation to {lang_info['name']} ({lang_info['native_name']})")
            
            # Translate transcript if available
            if 'transcript' in meeting_data and meeting_data['transcript']:
                print(f"📝 Processing transcript ({len(meeting_data['transcript'])} characters)")
                translations['transcript'] = self.translate_text(
                    meeting_data['transcript'], 
                    target_language, 
                    "transcript"
                )
            
            # Translate summary if available
            if 'summary' in meeting_data and meeting_data['summary']:
                print(f"📋 Processing summary ({len(meeting_data['summary'])} characters)")
                translations['summary'] = self.translate_text(
                    meeting_data['summary'], 
                    target_language, 
                    "summary"
                )
            
            # Translate action items if available
            if 'action_items' in meeting_data and meeting_data['action_items']:
                action_items_text = self._format_action_items_for_translation(meeting_data['action_items'])
                print(f"✅ Processing action items ({len(action_items_text)} characters)")
                translations['action_items'] = self.translate_text(
                    action_items_text, 
                    target_language, 
                    "action_items"
                )
            
            # Translate decisions if available
            if 'decisions' in meeting_data and meeting_data['decisions']:
                decisions_text = self._format_decisions_for_translation(meeting_data['decisions'])
                print(f"🎯 Processing decisions ({len(decisions_text)} characters)")
                translations['decisions'] = self.translate_text(
                    decisions_text, 
                    target_language, 
                    "decisions"
                )
            
            # Translate key topics if available
            if 'key_topics' in meeting_data and meeting_data['key_topics']:
                topics_text = self._format_topics_for_translation(meeting_data['key_topics'])
                print(f"🏷️ Processing key topics ({len(topics_text)} characters)")
                translations['key_topics'] = self.translate_text(
                    topics_text, 
                    target_language, 
                    "topics"
                )
            
            print(f"🎉 Translation completed! Generated {len(translations)} translations.")
            return {
                'target_language': target_language,
                'language_info': self.supported_languages[target_language],
                'translations': translations,
                'translation_complete': True
            }
            
        except Exception as e:
            print(f"❌ Translation failed: {str(e)}")
            return {
                'target_language': target_language,
                'translations': translations,
                'translation_complete': False,
                'error': str(e)
            }
    
    def _format_action_items_for_translation(self, action_items: List[Dict]) -> str:
        """Format action items for translation"""
        formatted = []
        for i, item in enumerate(action_items, 1):
            formatted.append(f"{i}. Task: {item.get('task', '')}")
            if item.get('owner'):
                formatted.append(f"   Owner: {item['owner']}")
            if item.get('deadline'):
                formatted.append(f"   Deadline: {item['deadline']}")
            if item.get('priority'):
                formatted.append(f"   Priority: {item['priority']}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_decisions_for_translation(self, decisions: List[Dict]) -> str:
        """Format decisions for translation"""
        formatted = []
        for i, decision in enumerate(decisions, 1):
            formatted.append(f"{i}. Decision: {decision.get('decision', '')}")
            if decision.get('context'):
                formatted.append(f"   Context: {decision['context']}")
            if decision.get('impact'):
                formatted.append(f"   Impact: {decision['impact']}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_topics_for_translation(self, topics: List[Dict]) -> str:
        """Format key topics for translation"""
        formatted = []
        for i, topic in enumerate(topics, 1):
            formatted.append(f"{i}. Topic: {topic.get('topic', '')}")
            if topic.get('discussion_points'):
                for point in topic['discussion_points']:
                    formatted.append(f"   - {point}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def detect_language(self, text: str) -> Dict:
        """
        Detect the language of input text using GPT-4
        """
        
        system_prompt = """You are a language detection expert. Analyze the provided text and identify its language.
        
        Respond with ONLY a JSON object in this format:
        {
            "detected_language": "language_name",
            "confidence": "high/medium/low",
            "language_code": "ISO_code",
            "notes": "any_relevant_notes"
        }"""
        
        user_prompt = f"Identify the language of this text:\n\n{text[:1000]}..."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(content)
                
        except Exception as e:
            return {
                "detected_language": "unknown",
                "confidence": "low", 
                "language_code": "unknown",
                "notes": f"Detection failed: {str(e)}"
            } 