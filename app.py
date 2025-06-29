from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
from werkzeug.utils import secure_filename
from config import Config
from database import DatabaseManager
from audio_processor import AudioProcessor
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
    
    return render_template('meeting_detail.html', meeting=meeting, transcription=transcription)

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

@app.errorhandler(413)
def too_large(e):
    flash("File is too large. Maximum size is 100MB.")
    return redirect(request.url)

if __name__ == '__main__':
    app.run(debug=True) 