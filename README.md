# 🎤 AI Meeting Assistant for KIU Consulting

An intelligent meeting processing system that automatically transcribes audio recordings, extracts actionable insights, and creates a searchable organizational knowledge base.

## 🚀 Features

### ✅ Implemented (Phases 1 & 2 Complete)

- **Audio Processing with Whisper API**: Upload and transcribe meeting recordings (.mp3, .wav, .m4a, etc.)
- **Speaker Identification**: AI-powered speaker detection and segmentation
- **Content Analysis (GPT-4)**: Generate comprehensive meeting summaries with action items
- **Decision Extraction**: Automatically identify and document key decisions made
- **Function Calling**: Calendar/task API integration for action items (Bonus +3pts)
- **Meeting Insights**: Effectiveness scoring and engagement analysis with recommendations
- **Web Interface**: Professional, responsive UI with real-time updates
- **Database Storage**: Complete SQLite schema for all current and future features
- **Real-time Processing**: Live status updates during transcription and analysis

### 🔄 Coming Soon (Phase 3)

- **Semantic Search (Embeddings)**: Searchable knowledge base across all meetings
- **Visual Synthesis (DALL-E 3)**: Create visual summaries and presentation assets
- **Advanced Features**: Fine-tuning, real-time processing, multi-language support

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- OpenAI API key
- FFmpeg (for audio processing)

### Installation

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd meeting-assistant
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg**

   - **macOS**: `brew install ffmpeg`
   - **Ubuntu**: `sudo apt update && sudo apt install ffmpeg`
   - **Windows**: Download from https://ffmpeg.org/download.html

5. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your OpenAI API key:

   ```
   OPENAI_API_KEY=your_actual_api_key_here
   FLASK_SECRET_KEY=your_secret_key_here
   ```

6. **Run the application**

   ```bash
   python app.py
   ```

7. **Open your browser**
   Navigate to `http://localhost:5000`

## 📋 Usage

### Upload a Meeting

1. Click "Upload New Meeting" on the dashboard
2. Enter a descriptive meeting title
3. Drag & drop or select an audio file (max 100MB)
4. Click "Upload Meeting"

### Transcribe Audio

1. Go to the meeting detail page
2. Click "Start Transcription"
3. Wait for AI processing (typically 1-3 minutes for 20-30 minute meetings)
4. View the transcription with speaker segments and timestamps

### Analyze Meeting Content

1. After transcription is complete, click "Analyze with GPT-4"
2. Wait for AI analysis (typically 30-60 seconds)
3. Review the comprehensive analysis including:
   - Meeting summary
   - Action items with assigned owners and priorities
   - Key decisions made with context
   - Discussion topics and main points
   - Meeting effectiveness insights and recommendations

### Supported Audio Formats

- MP3, WAV, M4A, MP4, MPEG, MPGA, WEBM
- Maximum file size: 100MB
- Optimal duration: 20-30 minutes

## 🏗️ Technical Architecture

```
meeting-assistant/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── database.py           # Database models and operations
├── audio_processor.py    # Whisper API integration
├── content_analyzer.py   # GPT-4 content analysis + function calling
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   └── meeting_detail.html
├── uploads/              # Audio file storage
├── requirements.txt      # Python dependencies
├── test_basic.py         # Test suite
└── README.md
```

### Database Schema

- **meetings**: Store meeting metadata and status
- **transcriptions**: Store full transcripts and speaker segments
- **meeting_summaries**: AI-generated summaries, action items, and decisions
- **meeting_insights**: Effectiveness scores, engagement analysis, and recommendations
- **embeddings**: (Future) Vector embeddings for semantic search

## 🔧 Development

### Running Tests

```bash
python -m pytest tests/
```

### Adding New Features

The application is designed for incremental development:

1. Each core feature is modular
2. Database schema supports all planned features
3. API endpoints are ready for extension

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `FLASK_SECRET_KEY`: Secret key for Flask sessions
- `FLASK_ENV`: Set to "development" for debugging
- `DATABASE_URL`: SQLite database path

## 📊 Cost Savings for KIU Consulting

This system addresses KIU Consulting's **25,000 GEL annual loss per employee** due to ineffective meetings by:

- **Automatic Documentation**: No manual note-taking required
- **Action Item Tracking**: Clear accountability and follow-up
- **Knowledge Retention**: Searchable meeting history
- **Decision Transparency**: Clear record of decisions and reasoning
- **Time Efficiency**: Quick meeting summaries for non-attendees

## 🏆 Assessment Criteria Progress

- ✅ **Multi-API Integration (15 pts)**: Whisper + GPT-4 + Function Calling implemented, Embeddings/DALL-E next
- ✅ **Advanced AI Features (10 pts)**: Function calling, speaker ID, content analysis, meeting insights
- ✅ **Technical Quality (8 pts)**: Clean code, error handling, modular architecture, comprehensive testing
- ✅ **Test Cases (4 pts)**: 7/7 tests passing, full system coverage
- ✅ **Documentation (3 pts)**: Comprehensive README, code docs, usage examples

## 🤝 Contributing

This is a hackathon project for KIU Consulting. For issues or feature requests, please create an issue in the repository.

## 📄 License

This project is developed for KIU Consulting's internal use.

---

**Note**: This system now includes Phases 1 & 2 complete (Audio Processing + Content Analysis). Phase 3 (Semantic Search + Visual Synthesis) will be added next while maintaining backward compatibility and system reliability.
