from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
from werkzeug.utils import secure_filename
from config import Config
from database import DatabaseManager
from audio_processor import AudioProcessor
from content_analyzer import ContentAnalyzer
from semantic_search import SemanticSearchEngine
from visual_synthesis import VisualSynthesisEngine
from translation_processor import TranslationProcessor
import json

app = Flask(__name__)
app.config.from_object(Config)

# Add custom template filters
@app.template_filter('nl2br')
def nl2br_filter(text):
    """Convert newlines to HTML line breaks"""
    if text is None:
        return ''
    return text.replace('\n', '<br>\n')

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
    visuals = db.get_meeting_visuals(meeting_id)
    translations = db.get_available_translation_languages(meeting_id)
    
    # Get supported languages for translation
    if app.config['OPENAI_API_KEY']:
        translator = TranslationProcessor(app.config['OPENAI_API_KEY'])
        supported_languages = translator.get_supported_languages()
    else:
        supported_languages = {}
    
    return render_template('meeting_detail.html', 
                         meeting=meeting, 
                         transcription=transcription,
                         summary=summary,
                         insights=insights,
                         visuals=visuals,
                         translations=translations,
                         supported_languages=supported_languages)

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

@app.route('/generate_visuals/<int:meeting_id>', methods=['POST'])
def generate_meeting_visuals(meeting_id):
    """Generate visual assets for a meeting using DALL-E 3"""
    if not app.config['OPENAI_API_KEY']:
        return jsonify({'error': 'OpenAI API key not configured'}), 400
    
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404
    
    summary = db.get_meeting_summary(meeting_id)
    if not summary:
        return jsonify({'error': 'Meeting must be analyzed first'}), 400
    
    try:
        visual_engine = VisualSynthesisEngine(app.config['OPENAI_API_KEY'])
        
        # Prepare meeting data for visual generation
        meeting_data = {
            'title': meeting['title'],
            'summary': summary['summary'],
            'action_items': summary.get('action_items', []),
            'decisions': summary.get('decisions', []),
            'key_topics': summary.get('key_topics', [])
        }
        
        # Generate complete visual presentation pack
        visual_pack = visual_engine.create_visual_presentation_pack(meeting_id, meeting_data)
        
        # Save successful visuals to database
        saved_visuals = []
        for visual_item in visual_pack:
            if visual_item['visual']['success']:
                visual_data = visual_item['visual'].copy()
                visual_data['title'] = visual_item['title']
                visual_data['image_size'] = visual_engine.image_size
                
                visual_id = db.save_visual_asset(meeting_id, visual_data)
                saved_visuals.append({
                    'id': visual_id,
                    'type': visual_item['type'],
                    'title': visual_item['title']
                })
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(saved_visuals)} visual assets successfully',
            'visuals': saved_visuals
        })
        
    except Exception as e:
        return jsonify({'error': f'Visual generation failed: {str(e)}'}), 500

@app.route('/visual/<int:visual_id>')
def view_visual(visual_id):
    """View a specific visual asset"""
    visual = db.get_visual_asset(visual_id)
    if not visual:
        flash('Visual asset not found')
        return redirect(url_for('index'))
    
    meeting = db.get_meeting(visual['meeting_id'])
    return render_template('visual_detail.html', visual=visual, meeting=meeting)

@app.route('/meeting/<int:meeting_id>/visuals')
def meeting_visuals(meeting_id):
    """View all visual assets for a meeting"""
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        flash('Meeting not found')
        return redirect(url_for('index'))
    
    visuals = db.get_meeting_visuals(meeting_id)
    return render_template('meeting_visuals.html', meeting=meeting, visuals=visuals)

@app.route('/visuals')
def visual_gallery():
    """Gallery of all visual assets"""
    # Get visuals by type
    summaries = db.get_all_visuals_by_type('meeting_summary')
    action_items = db.get_all_visuals_by_type('action_items')
    decisions = db.get_all_visuals_by_type('decisions')
    infographics = db.get_all_visuals_by_type('infographic')
    
    return render_template('visual_gallery.html', 
                         summaries=summaries,
                         action_items=action_items,
                         decisions=decisions,
                         infographics=infographics)

@app.route('/generate_single_visual/<int:meeting_id>', methods=['POST'])
def generate_single_visual(meeting_id):
    """Generate a single visual of specified type"""
    if not app.config['OPENAI_API_KEY']:
        return jsonify({'error': 'OpenAI API key not configured'}), 400
    
    visual_type = request.form.get('visual_type')
    style = request.form.get('style', 'professional')
    
    if not visual_type:
        return jsonify({'error': 'Visual type is required'}), 400
    
    meeting = db.get_meeting(meeting_id)
    summary = db.get_meeting_summary(meeting_id)
    
    if not meeting or not summary:
        return jsonify({'error': 'Meeting and analysis data required'}), 400
    
    try:
        visual_engine = VisualSynthesisEngine(app.config['OPENAI_API_KEY'])
        
        result = None
        title = ""
        
        if visual_type == 'summary':
            key_points = [topic.get('topic', topic) if isinstance(topic, dict) else str(topic) 
                         for topic in summary.get('key_topics', [])[:5]]
            result = visual_engine.generate_meeting_visual_summary(
                meeting['title'], summary['summary'], key_points, style
            )
            title = "Meeting Overview"
            
        elif visual_type == 'action_items':
            if not summary.get('action_items'):
                return jsonify({'error': 'No action items found'}), 400
            result = visual_engine.generate_action_items_visual(
                summary['action_items'], meeting['title'], style
            )
            title = "Action Items & Next Steps"
            
        elif visual_type == 'decisions':
            if not summary.get('decisions'):
                return jsonify({'error': 'No decisions found'}), 400
            result = visual_engine.generate_decisions_visual(
                summary['decisions'], meeting['title'], style
            )
            title = "Key Decisions Made"
            
        elif visual_type == 'infographic':
            meeting_data = {
                'title': meeting['title'],
                'summary': summary['summary'],
                'action_items': summary.get('action_items', []),
                'decisions': summary.get('decisions', []),
                'key_topics': summary.get('key_topics', [])
            }
            result = visual_engine.generate_meeting_infographic(meeting_data, style)
            title = "Meeting Infographic"
            
        else:
            return jsonify({'error': 'Invalid visual type'}), 400
        
        if result and result['success']:
            # Save to database
            visual_data = result.copy()
            visual_data['title'] = title
            visual_data['image_size'] = visual_engine.image_size
            
            visual_id = db.save_visual_asset(meeting_id, visual_data)
            
            return jsonify({
                'success': True,
                'message': f'{title} generated successfully',
                'visual_id': visual_id,
                'image_url': result['image_url']
            })
        else:
            return jsonify({'error': result.get('error', 'Unknown error')}), 500
            
    except Exception as e:
        return jsonify({'error': f'Visual generation failed: {str(e)}'}), 500

@app.route('/delete_visual/<int:visual_id>', methods=['POST'])
def delete_visual(visual_id):
    """Delete a visual asset"""
    visual = db.get_visual_asset(visual_id)
    if not visual:
        return jsonify({'error': 'Visual not found'}), 404
    
    try:
        db.delete_visual_asset(visual_id)
        return jsonify({'success': True, 'message': 'Visual deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500

@app.route('/translate/<int:meeting_id>', methods=['POST'])
def translate_meeting(meeting_id):
    """Translate meeting content to target language"""
    print(f"\n🔄 Translation request received for meeting {meeting_id}")
    
    if not app.config['OPENAI_API_KEY']:
        return jsonify({'error': 'OpenAI API key not configured'}), 400
    
    target_language = request.form.get('target_language')
    content_types = request.form.getlist('content_types')
    
    print(f"📝 Target language: {target_language}")
    print(f"📋 Content types: {content_types}")
    
    if not target_language:
        return jsonify({'error': 'Target language is required'}), 400
    
    if not content_types:
        return jsonify({'error': 'At least one content type must be selected'}), 400
    
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404
    
    try:
        print("🤖 Initializing translation processor...")
        translator = TranslationProcessor(app.config['OPENAI_API_KEY'])
        
        print("📦 Preparing meeting data for translation...")
        # Prepare meeting data for translation
        meeting_data = {}
        
        if 'transcript' in content_types:
            transcription = db.get_transcription(meeting_id)
            if transcription:
                meeting_data['transcript'] = transcription['full_text']
        
        if 'summary' in content_types:
            summary = db.get_meeting_summary(meeting_id)
            if summary:
                meeting_data['summary'] = summary['summary']
                
                if 'action_items' in content_types:
                    meeting_data['action_items'] = summary.get('action_items', [])
                
                if 'decisions' in content_types:
                    meeting_data['decisions'] = summary.get('decisions', [])
                    
                if 'key_topics' in content_types:
                    meeting_data['key_topics'] = summary.get('key_topics', [])
        
        if not meeting_data:
            print("❌ No content available for translation")
            return jsonify({'error': 'No content available for translation'}), 400
        
        print(f"🚀 Starting translation with {len(meeting_data)} content types")
        # Perform translation
        translation_result = translator.translate_meeting_content(meeting_data, target_language)
        print("✅ Translation completed, processing results...")
        
        if not translation_result['translation_complete']:
            return jsonify({'error': f"Translation failed: {translation_result.get('error', 'Unknown error')}"}), 500
        
        # Save translations to database
        saved_translations = []
        for content_type, translation_data in translation_result['translations'].items():
            original_text = meeting_data[content_type]
            if isinstance(original_text, list):
                original_text = str(original_text)  # Convert lists to string for storage
            
            translation_id = db.save_translation(
                meeting_id, 
                content_type, 
                original_text, 
                translation_data
            )
            saved_translations.append({
                'id': translation_id,
                'content_type': content_type,
                'language': translation_data['language_name']
            })
        
        return jsonify({
            'success': True,
            'message': f'Content translated to {translation_result["language_info"]["name"]} successfully',
            'translations': saved_translations,
            'language_info': translation_result['language_info']
        })
        
    except Exception as e:
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

@app.route('/meeting/<int:meeting_id>/translations')
def view_meeting_translations(meeting_id):
    """View all translations for a meeting"""
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        flash('Meeting not found')
        return redirect(url_for('index'))
    
    translations = db.get_meeting_translations(meeting_id)
    available_languages = db.get_available_translation_languages(meeting_id)
    
    # Group translations by language
    translations_by_language = {}
    for translation in translations:
        lang_key = translation['target_language']
        if lang_key not in translations_by_language:
            translations_by_language[lang_key] = {
                'language_info': {
                    'name': translation['language_name'],
                    'code': translation['language_code'],
                    'native_name': translation['native_name']
                },
                'translations': []
            }
        translations_by_language[lang_key]['translations'].append(translation)
    
    return render_template('meeting_translations.html', 
                         meeting=meeting,
                         translations_by_language=translations_by_language,
                         available_languages=available_languages)

@app.route('/meeting/<int:meeting_id>/translation/<target_language>')
def view_single_language_translation(meeting_id, target_language):
    """View translations for a specific language"""
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        flash('Meeting not found')
        return redirect(url_for('index'))
    
    translations = db.get_meeting_translations(meeting_id, target_language)
    if not translations:
        flash(f'No translations found for {target_language}')
        return redirect(url_for('view_meeting', meeting_id=meeting_id))
    
    # Group by content type
    translations_by_type = {}
    language_info = None
    for translation in translations:
        content_type = translation['content_type']
        translations_by_type[content_type] = translation
        if not language_info:
            language_info = {
                'name': translation['language_name'],
                'code': translation['language_code'],
                'native_name': translation['native_name']
            }
    
    return render_template('single_language_translation.html',
                         meeting=meeting,
                         translations_by_type=translations_by_type,
                         language_info=language_info,
                         target_language=target_language)

@app.route('/search_translations', methods=['GET', 'POST'])
def search_translations():
    """Search within translated content"""
    if request.method == 'POST':
        search_query = request.form.get('query', '').strip()
        target_language = request.form.get('language', '')
        
        if not search_query:
            flash('Please enter a search query')
            return redirect(request.url)
        
        # Perform search
        if target_language:
            results = db.search_translations(search_query, target_language)
        else:
            results = db.search_translations(search_query)
        
        # Get available languages for filter
        if app.config['OPENAI_API_KEY']:
            translator = TranslationProcessor(app.config['OPENAI_API_KEY'])
            supported_languages = translator.get_supported_languages()
        else:
            supported_languages = {}
        
        return render_template('translation_search_results.html',
                             search_query=search_query,
                             results=results,
                             target_language=target_language,
                             supported_languages=supported_languages)
    
    # GET request - show search form
    if app.config['OPENAI_API_KEY']:
        translator = TranslationProcessor(app.config['OPENAI_API_KEY'])
        supported_languages = translator.get_supported_languages()
    else:
        supported_languages = {}
    
    return render_template('translation_search.html', supported_languages=supported_languages)

@app.route('/delete_translation/<int:translation_id>', methods=['POST'])
def delete_translation(translation_id):
    """Delete a specific translation"""
    translation = db.get_translation_by_id(translation_id)
    if not translation:
        return jsonify({'error': 'Translation not found'}), 404
    
    try:
        # For now, we'll delete from database directly
        # In production, you might want to implement soft delete
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM translations WHERE id = ?', (translation_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Translation deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    flash("File is too large. Maximum size is 100MB.")
    return redirect(request.url)

if __name__ == '__main__':
    app.run(debug=True) 