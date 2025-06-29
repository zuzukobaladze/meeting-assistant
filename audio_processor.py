import os
import openai
from typing import Dict, List, Tuple
import json
import tempfile

class AudioProcessor:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    def get_audio_duration(self, file_path: str) -> float:
        """Get audio file duration in seconds"""
        try:
            # Use a more direct approach for getting duration
            import os
            file_size = os.path.getsize(file_path)
            # Estimate duration based on file size (rough approximation)
            # For a more accurate duration, we'll get it from the transcription API
            return None  # Will be set after transcription
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return None
    
    def preprocess_audio(self, file_path: str) -> str:
        """Preprocess audio file if needed - simplified version"""
        try:
            # For now, we'll trust that OpenAI Whisper can handle the file as-is
            # Whisper is quite robust with different audio formats
            # In a production system, you might want to add ffmpeg preprocessing here
            return file_path
        except Exception as e:
            print(f"Error preprocessing audio: {e}")
            return file_path
    
    def transcribe_audio(self, file_path: str, enable_speaker_detection: bool = True) -> Dict:
        """
        Transcribe audio using OpenAI Whisper API
        Returns transcription with speaker identification if enabled
        """
        try:
            # Preprocess audio
            processed_file = self.preprocess_audio(file_path)
            
            # Open audio file
            with open(processed_file, 'rb') as audio_file:
                # Basic transcription
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            # Clean up temporary file if created
            if processed_file != file_path:
                os.unlink(processed_file)
            
            # Process the response
            result = {
                'text': transcript.text,
                'language': transcript.language,
                'duration': transcript.duration,
                'segments': []
            }
            
            # Process segments
            for segment in transcript.segments:
                segment_data = {
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'speaker': self._detect_speaker_simple(segment.text) if enable_speaker_detection else 'Unknown'
                }
                result['segments'].append(segment_data)
            
            return result
            
        except Exception as e:
            raise Exception(f"Error transcribing audio: {str(e)}")
    
    def _detect_speaker_simple(self, text: str) -> str:
        """
        Simple speaker detection based on text patterns
        In a production system, this would use more sophisticated speaker diarization
        """
        # Simple heuristics for speaker detection
        # This is a placeholder - in reality you'd use speaker diarization models
        
        # Look for first-person pronouns
        first_person_indicators = ['I ', ' I ', 'my ', 'me ', 'myself']
        if any(indicator in text.lower() for indicator in first_person_indicators):
            return 'Speaker A'
        
        # Look for question patterns
        if '?' in text or text.lower().startswith(('what', 'how', 'when', 'where', 'why', 'who')):
            return 'Speaker B'
        
        # Default to alternating speakers based on segment index
        return 'Speaker A'
    
    def extract_highlights(self, segments: List[Dict], threshold_duration: float = 5.0) -> List[Dict]:
        """Extract key highlights from transcription segments"""
        highlights = []
        
        for segment in segments:
            duration = segment['end'] - segment['start']
            text = segment['text'].strip()
            
            # Consider segments with certain keywords or longer duration as highlights
            keywords = ['action', 'decision', 'next steps', 'follow up', 'deadline', 'responsible']
            
            if (duration > threshold_duration or 
                any(keyword in text.lower() for keyword in keywords)):
                highlights.append({
                    'timestamp': f"{segment['start']:.1f}s - {segment['end']:.1f}s",
                    'speaker': segment['speaker'],
                    'text': text,
                    'importance': 'high' if any(keyword in text.lower() for keyword in keywords) else 'medium'
                })
        
        return highlights
    
    def format_transcription_display(self, segments: List[Dict]) -> str:
        """Format transcription for display with timestamps and speakers"""
        formatted_text = ""
        current_speaker = None
        
        for segment in segments:
            speaker = segment['speaker']
            timestamp = f"[{segment['start']:.1f}s]"
            
            if speaker != current_speaker:
                formatted_text += f"\n\n**{speaker}** {timestamp}:\n"
                current_speaker = speaker
            
            formatted_text += f"{segment['text']} "
        
        return formatted_text.strip() 