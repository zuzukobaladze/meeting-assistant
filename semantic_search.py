import openai
import numpy as np
import json
from typing import Dict, List, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
import re

class SemanticSearchEngine:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.embedding_model = "text-embedding-3-small"  # Latest OpenAI embedding model
        self.chunk_size = 1000  # Characters per chunk for better granularity
        
    def chunk_text(self, text: str, chunk_size: int = None) -> List[str]:
        """Split text into overlapping chunks for better semantic coverage"""
        if chunk_size is None:
            chunk_size = self.chunk_size
            
        # Split by sentences to maintain semantic coherence
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed chunk size, save current chunk
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using OpenAI API"""
        try:
            # OpenAI embeddings API can handle multiple texts at once
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
                encoding_format="float"
            )
            
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as e:
            raise Exception(f"Error generating embeddings: {str(e)}")
    
    def process_meeting_for_search(self, meeting_id: int, transcription_text: str, 
                                 meeting_title: str = "", summary: str = "") -> List[Dict]:
        """Process a meeting to create searchable chunks with embeddings"""
        
        # Create enhanced text combining different sources
        enhanced_texts = []
        
        # Main transcription chunks
        transcription_chunks = self.chunk_text(transcription_text)
        for i, chunk in enumerate(transcription_chunks):
            enhanced_text = f"Meeting: {meeting_title}\n\nContent: {chunk}"
            enhanced_texts.append({
                'meeting_id': meeting_id,
                'chunk_type': 'transcription',
                'chunk_index': i,
                'text': chunk,
                'enhanced_text': enhanced_text,
                'metadata': {'title': meeting_title, 'type': 'transcription'}
            })
        
        # Summary as a separate searchable item
        if summary:
            enhanced_text = f"Meeting: {meeting_title}\n\nSummary: {summary}"
            enhanced_texts.append({
                'meeting_id': meeting_id,
                'chunk_type': 'summary',
                'chunk_index': 0,
                'text': summary,
                'enhanced_text': enhanced_text,
                'metadata': {'title': meeting_title, 'type': 'summary'}
            })
        
        # Generate embeddings for all enhanced texts
        texts_for_embedding = [item['enhanced_text'] for item in enhanced_texts]
        
        try:
            embeddings = self.generate_embeddings(texts_for_embedding)
            
            # Combine text data with embeddings
            for i, item in enumerate(enhanced_texts):
                item['embedding'] = embeddings[i]
                
            return enhanced_texts
            
        except Exception as e:
            print(f"Warning: Could not generate embeddings for meeting {meeting_id}: {e}")
            return []
    
    def search_meetings(self, query: str, all_embeddings: List[Dict], 
                       top_k: int = 10, similarity_threshold: float = 0.7) -> List[Dict]:
        """Search across all meetings using semantic similarity"""
        
        try:
            # Generate embedding for the search query
            query_embedding = self.generate_embeddings([query])[0]
            
            # Calculate similarities
            results = []
            for item in all_embeddings:
                # Calculate cosine similarity
                similarity = cosine_similarity(
                    [query_embedding], 
                    [item['embedding']]
                )[0][0]
                
                if similarity >= similarity_threshold:
                    results.append({
                        'meeting_id': item['meeting_id'],
                        'chunk_type': item['chunk_type'],
                        'chunk_index': item['chunk_index'],
                        'text': item['text'],
                        'similarity': float(similarity),
                        'metadata': item['metadata']
                    })
            
            # Sort by similarity (highest first) and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            raise Exception(f"Error during semantic search: {str(e)}")
    
    def find_similar_meetings(self, meeting_id: int, meeting_embeddings: List[Dict],
                            all_embeddings: List[Dict], top_k: int = 5) -> List[Dict]:
        """Find meetings similar to a given meeting"""
        
        # Get embeddings for the target meeting
        target_embeddings = [item for item in meeting_embeddings if item['meeting_id'] == meeting_id]
        
        if not target_embeddings:
            return []
        
        # Calculate average embedding for the target meeting
        target_vectors = [item['embedding'] for item in target_embeddings]
        avg_target_embedding = np.mean(target_vectors, axis=0)
        
        # Find similar meetings
        meeting_similarities = {}
        for item in all_embeddings:
            if item['meeting_id'] != meeting_id:  # Exclude the target meeting itself
                similarity = cosine_similarity(
                    [avg_target_embedding], 
                    [item['embedding']]
                )[0][0]
                
                if item['meeting_id'] not in meeting_similarities:
                    meeting_similarities[item['meeting_id']] = []
                meeting_similarities[item['meeting_id']].append(similarity)
        
        # Calculate average similarity for each meeting
        meeting_scores = []
        for mid, similarities in meeting_similarities.items():
            avg_similarity = np.mean(similarities)
            meeting_scores.append({
                'meeting_id': mid,
                'similarity': float(avg_similarity),
                'match_count': len(similarities)
            })
        
        # Sort by similarity and return top results
        meeting_scores.sort(key=lambda x: x['similarity'], reverse=True)
        return meeting_scores[:top_k]
    
    def discover_cross_meeting_insights(self, all_embeddings: List[Dict], 
                                       themes: List[str] = None) -> Dict[str, List[Dict]]:
        """Discover insights across meetings for specific themes"""
        
        if themes is None:
            themes = [
                "action items and follow-ups",
                "key decisions and outcomes", 
                "challenges and problems discussed",
                "project updates and status",
                "team collaboration and communication"
            ]
        
        insights = {}
        
        for theme in themes:
            try:
                # Search for each theme across all meetings
                theme_results = self.search_meetings(
                    theme, 
                    all_embeddings, 
                    top_k=15, 
                    similarity_threshold=0.6
                )
                
                # Group by meeting and aggregate
                meeting_groups = {}
                for result in theme_results:
                    mid = result['meeting_id']
                    if mid not in meeting_groups:
                        meeting_groups[mid] = {
                            'meeting_id': mid,
                            'total_similarity': 0,
                            'relevant_chunks': [],
                            'title': result['metadata'].get('title', 'Unknown Meeting')
                        }
                    
                    meeting_groups[mid]['total_similarity'] += result['similarity']
                    meeting_groups[mid]['relevant_chunks'].append({
                        'text': result['text'][:200] + "..." if len(result['text']) > 200 else result['text'],
                        'similarity': result['similarity'],
                        'type': result['chunk_type']
                    })
                
                # Sort and format results
                theme_insights = list(meeting_groups.values())
                theme_insights.sort(key=lambda x: x['total_similarity'], reverse=True)
                insights[theme] = theme_insights[:8]  # Top 8 meetings per theme
                
            except Exception as e:
                print(f"Warning: Could not analyze theme '{theme}': {e}")
                insights[theme] = []
        
        return insights
    
    def generate_meeting_recommendations(self, meeting_id: int, meeting_title: str,
                                       similar_meetings: List[Dict], 
                                       cross_insights: Dict) -> Dict:
        """Generate personalized recommendations based on meeting content"""
        
        recommendations = {
            'similar_meetings': [],
            'related_topics': [],
            'action_suggestions': [],
            'follow_up_meetings': []
        }
        
        # Process similar meetings
        for similar in similar_meetings[:3]:  # Top 3 similar meetings
            recommendations['similar_meetings'].append({
                'meeting_id': similar['meeting_id'],
                'similarity_score': similar['similarity'],
                'reason': f"Similar content and topics discussed ({similar['similarity']:.1%} match)"
            })
        
        # Extract related topics from cross-insights
        for theme, insights in cross_insights.items():
            if insights:  # If this meeting appears in theme insights
                relevant_meetings = [i for i in insights if i['meeting_id'] != meeting_id]
                if relevant_meetings:
                    recommendations['related_topics'].append({
                        'theme': theme,
                        'related_meetings_count': len(relevant_meetings),
                        'top_meeting_id': relevant_meetings[0]['meeting_id'] if relevant_meetings else None
                    })
        
        # Generate action suggestions based on patterns
        if any('action' in theme.lower() for theme in cross_insights.keys()):
            recommendations['action_suggestions'].append(
                "Review action items from similar meetings to ensure consistency"
            )
            recommendations['action_suggestions'].append(
                "Consider scheduling follow-up meetings for unresolved topics"
            )
        
        return recommendations 