from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
from werkzeug.utils import secure_filename
from config import Config
from database import DatabaseManager
from audio_processor import AudioProcessor
from content_analyzer import ContentAnalyzer
from semantic_search import SemanticSearchEngine
import json

app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
db = DatabaseManager()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Main dashboard showing all meetings"""
    meetings = db.get_all_meetings()
    return render_template('index.html', meetings=meetings)

@app.route('/upload', methods=['GET', 'POST'])
def upload_meeting():
    """Upload meeting audio file"""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'audio_file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['audio_file']
        meeting_title = request.form.get('meeting_title', '').strip()
        
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if not meeting_title:
            flash('Please provide a meeting title')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Duration will be determined during transcription
            duration = None
            
            # Save to database
            meeting_id = db.create_meeting(meeting_title, filename, file_path, duration)
            
            flash(f'Meeting "{meeting_title}" uploaded successfully!')
            return redirect(url_for('view_meeting', meeting_id=meeting_id))
        else:
            flash('Invalid file type. Please upload an audio file (mp3, wav, m4a, etc.)')
    
    return render_template('upload.html')

@app.route('/meeting/<int:meeting_id>')
def view_meeting(meeting_id):
    """View meeting details and transcription"""
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        flash('Meeting not found')
        return redirect(url_for('index'))
    
    transcription = db.get_transcription(meeting_id)
    summary = db.get_meeting_summary(meeting_id)
    insights = db.get_meeting_insights(meeting_id)
    
    return render_template('meeting_detail.html', 
                         meeting=meeting, 
                         transcription=transcription,
                         summary=summary,
                         insights=insights)

@app.route('/transcribe/<int:meeting_id>', methods=['POST'])
def transcribe_meeting(meeting_id):
    """Transcribe a meeting audio file"""
    if not app.config['OPENAI_API_KEY']:
        return jsonify({'error': 'OpenAI API key not configured'}), 400
    
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404
    
    try:
        # Update status to processing
        db.update_meeting_status(meeting_id, 'processing')
        
        # Initialize audio processor
        processor = AudioProcessor(app.config['OPENAI_API_KEY'])
        
        # Transcribe the audio
        result = processor.transcribe_audio(meeting['file_path'])
        
        # Save transcription to database
        db.save_transcription(
            meeting_id,
            result['text'],
            result['segments'],
            result.get('language'),
            None,  # confidence score not available in current Whisper API
            result.get('duration')  # duration from Whisper API
        )
        
        return jsonify({
            'success': True,
            'message': 'Transcription completed successfully',
            'transcription': {
                'text': result['text'],
                'language': result.get('language'),
                'duration': result.get('duration'),
                'segments_count': len(result['segments'])
            }
        })
        
    except Exception as e:
        # Update status to error
        db.update_meeting_status(meeting_id, 'error')
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

@app.route('/analyze/<int:meeting_id>', methods=['POST'])
def analyze_meeting(meeting_id):
    """Analyze meeting content using GPT-4"""
    if not app.config['OPENAI_API_KEY']:
        return jsonify({'error': 'OpenAI API key not configured'}), 400
    
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404
    
    transcription = db.get_transcription(meeting_id)
    if not transcription:
        return jsonify({'error': 'Meeting must be transcribed first'}), 400
    
    try:
        # Initialize content analyzer
        analyzer = ContentAnalyzer(app.config['OPENAI_API_KEY'])
        
        # Analyze meeting content
        analysis = analyzer.analyze_meeting(
            transcription['full_text'], 
            meeting['title']
        )
        
        # Extract insights
        insights = analyzer.extract_meeting_insights(transcription['full_text'])
        
        # Enhance action items with function calling
        enhanced_action_items = analyzer.generate_action_items_with_calendar(
            analysis.get('action_items', []),
            meeting['uploaded_at'][:10]  # Use upload date as meeting date
        )
        
        # Save results to database
        db.save_meeting_summary(
            meeting_id,
            analysis['summary'],
            enhanced_action_items,
            analysis.get('decisions', []),
            analysis.get('key_topics', [])
        )
        
        db.save_meeting_insights(meeting_id, insights)
        
        # Generate embeddings for semantic search (auto-trigger)
        try:
            search_engine = SemanticSearchEngine(app.config['OPENAI_API_KEY'])
            summary = db.get_meeting_summary(meeting_id)
            summary_text = summary['summary'] if summary else ""
            
            embeddings_data = search_engine.process_meeting_for_search(
                meeting_id, 
                transcription['full_text'],
                meeting['title'],
                summary_text
            )
            
            if embeddings_data:
                db.save_embeddings(meeting_id, embeddings_data)
        
        except Exception as e:
            print(f"Warning: Could not generate embeddings for meeting {meeting_id}: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Meeting analysis completed successfully',
            'analysis': {
                'summary_length': len(analysis['summary']),
                'action_items_count': len(enhanced_action_items),
                'decisions_count': len(analysis.get('decisions', [])),
                'key_topics_count': len(analysis.get('key_topics', [])),
                'effectiveness_score': insights.get('effectiveness_score', 'N/A')
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/meetings')
def api_meetings():
    """API endpoint to get all meetings"""
    meetings = db.get_all_meetings()
    return jsonify(meetings)

@app.route('/api/meeting/<int:meeting_id>/transcription')
def api_transcription(meeting_id):
    """API endpoint to get meeting transcription"""
    transcription = db.get_transcription(meeting_id)
    if transcription:
        return jsonify(transcription)
    return jsonify({'error': 'Transcription not found'}), 404

@app.route('/search', methods=['GET', 'POST'])
def search_meetings():
    """Search meetings using semantic search"""
    if request.method == 'POST':
        search_query = request.form.get('query', '').strip()
        if not search_query:
            flash('Please enter a search query')
            return redirect(url_for('search_meetings'))
        
        return redirect(url_for('search_meetings', q=search_query))
    
    # GET request with query parameter
    search_query = request.args.get('q', '').strip()
    results = []
    similar_meetings = []
    cross_insights = {}
    
    if search_query:
        try:
            if not app.config['OPENAI_API_KEY']:
                flash('OpenAI API key not configured')
                return render_template('search_results.html', 
                                     query=search_query, 
                                     results=[], 
                                     fallback_results=db.search_meetings_by_text(search_query))
            
            search_engine = SemanticSearchEngine(app.config['OPENAI_API_KEY'])
            all_embeddings = db.get_all_embeddings()
            
            if not all_embeddings:
                flash('No embeddings found. Please analyze meetings first to enable semantic search.')
                return render_template('search_results.html', 
                                     query=search_query, 
                                     results=[], 
                                     fallback_results=db.search_meetings_by_text(search_query))
            
            # Perform semantic search
            results = search_engine.search_meetings(search_query, all_embeddings, top_k=15)
            
            # Get cross-meeting insights
            cross_insights = search_engine.discover_cross_meeting_insights(all_embeddings)
            
        except Exception as e:
            flash(f'Search error: {str(e)}')
            # Fallback to basic text search
            results = []
            fallback_results = db.search_meetings_by_text(search_query)
            return render_template('search_results.html', 
                                 query=search_query, 
                                 results=results,
                                 fallback_results=fallback_results)
    
    return render_template('search_results.html', 
                         query=search_query, 
                         results=results,
                         cross_insights=cross_insights)

@app.route('/meeting/<int:meeting_id>/similar')
def similar_meetings(meeting_id):
    """Find meetings similar to the given meeting"""
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        flash('Meeting not found')
        return redirect(url_for('index'))
    
    try:
        if not app.config['OPENAI_API_KEY']:
            flash('OpenAI API key not configured')
            return redirect(url_for('view_meeting', meeting_id=meeting_id))
        
        search_engine = SemanticSearchEngine(app.config['OPENAI_API_KEY'])
        all_embeddings = db.get_all_embeddings()
        meeting_embeddings = db.get_meeting_embeddings(meeting_id)
        
        if not all_embeddings or not meeting_embeddings:
            flash('Embeddings not found. Please analyze meetings first.')
            return redirect(url_for('view_meeting', meeting_id=meeting_id))
        
        # Find similar meetings
        similar = search_engine.find_similar_meetings(meeting_id, meeting_embeddings, all_embeddings)
        
        # Get cross-meeting insights
        cross_insights = search_engine.discover_cross_meeting_insights(all_embeddings)
        
        # Generate recommendations
        recommendations = search_engine.generate_meeting_recommendations(
            meeting_id, meeting['title'], similar, cross_insights
        )
        
        return render_template('similar_meetings.html',
                             meeting=meeting,
                             similar_meetings=similar,
                             recommendations=recommendations,
                             cross_insights=cross_insights)
        
    except Exception as e:
        flash(f'Error finding similar meetings: {str(e)}')
        return redirect(url_for('view_meeting', meeting_id=meeting_id))

@app.route('/insights')
def cross_meeting_insights():
    """View cross-meeting insights dashboard"""
    try:
        if not app.config['OPENAI_API_KEY']:
            flash('OpenAI API key not configured')
            return redirect(url_for('index'))
        
        search_engine = SemanticSearchEngine(app.config['OPENAI_API_KEY'])
        all_embeddings = db.get_all_embeddings()
        
        if not all_embeddings:
            flash('No embeddings found. Please analyze meetings first.')
            return redirect(url_for('index'))
        
        # Get cross-meeting insights
        insights = search_engine.discover_cross_meeting_insights(all_embeddings)
        
        # Get meeting titles for display
        meetings = {m['id']: m for m in db.get_all_meetings()}
        
        return render_template('insights.html', 
                             insights=insights,
                             meetings=meetings)
        
    except Exception as e:
        flash(f'Error generating insights: {str(e)}')
        return redirect(url_for('index'))

@app.route('/generate_embeddings/<int:meeting_id>', methods=['POST'])
def generate_embeddings(meeting_id):
    """Generate embeddings for a specific meeting"""
    if not app.config['OPENAI_API_KEY']:
        return jsonify({'error': 'OpenAI API key not configured'}), 400
    
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404
    
    transcription = db.get_transcription(meeting_id)
    if not transcription:
        return jsonify({'error': 'Meeting must be transcribed first'}), 400
    
    try:
        search_engine = SemanticSearchEngine(app.config['OPENAI_API_KEY'])
        summary = db.get_meeting_summary(meeting_id)
        summary_text = summary['summary'] if summary else ""
        
        embeddings_data = search_engine.process_meeting_for_search(
            meeting_id,
            transcription['full_text'],
            meeting['title'],
            summary_text
        )
        
        if embeddings_data:
            db.save_embeddings(meeting_id, embeddings_data)
            return jsonify({
                'success': True,
                'message': 'Embeddings generated successfully',
                'embeddings_count': len(embeddings_data)
            })
        else:
            return jsonify({'error': 'Failed to generate embeddings'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error generating embeddings: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    flash("File is too large. Maximum size is 100MB.")
    return redirect(request.url)

if __name__ == '__main__':
    app.run(debug=True) 