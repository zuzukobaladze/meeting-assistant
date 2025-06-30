# 🎤 AI Meeting Assistant for KIU Consulting

An intelligent meeting processing system that automatically transcribes audio recordings, extracts actionable insights, and creates a searchable organizational knowledge base.

## 🚀 Features

### ✅ Implemented (Phases 1, 2 & 3 Complete)

- **Audio Processing with Whisper API**: Upload and transcribe meeting recordings (.mp3, .wav, .m4a, etc.)
- **Speaker Identification**: AI-powered speaker detection and segmentation
- **Content Analysis (GPT-4)**: Generate comprehensive meeting summaries with action items
- **Decision Extraction**: Automatically identify and document key decisions made
- **Function Calling**: Calendar/task API integration for action items (Bonus +3pts)
- **Meeting Insights**: Effectiveness scoring and engagement analysis with recommendations
- **Semantic Search (Embeddings)**: AI-powered searchable knowledge base across all meetings
- **Cross-Meeting Discovery**: Find patterns, themes, and insights across meetings (Bonus +2pts)
- **Similarity Recommendations**: AI-powered meeting recommendations and connections
- **Translation Support (GPT-4)**: Translate meeting content to low-resource languages
- **Multi-Language Search**: Search across translated content in multiple languages
- **Web Interface**: Professional, responsive UI with real-time updates and advanced search
- **Database Storage**: Complete SQLite schema with vector embeddings support
- **Visual Synthesis (DALL-E 3)**: Create visual summaries and presentation assets
- **Advanced Features**: Multi-language support, translation, searching




## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- OpenAI API key
- FFmpeg (for audio processing)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/zuzukobaladze/meeting-assistant
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

### Search Across Meetings (Phase 3)

1. **Semantic Search**: Use the "Search" button in navigation

   - Search for concepts like "action items", "budget discussions", "team decisions"
   - AI understands meaning, not just keywords
   - View similarity scores and relevant content excerpts

2. **Find Similar Meetings**: From any meeting detail page

   - Click "Find Similar Meetings" button
   - See AI-generated recommendations and connections
   - Discover related content across your meeting history

3. **Cross-Meeting Insights**: Visit the "Insights" dashboard
   - Explore patterns and themes across all meetings
   - View AI-generated meeting relationship networks
   - Get optimization recommendations for meeting effectiveness

### Generate Visual Assets (Phase 4)

1. **Complete Visual Pack**: After meeting analysis

   - Click "Generate Visuals" button on meeting detail page
   - AI creates comprehensive visual presentation pack
   - Includes summary visuals, action item boards, decision trees, and infographics

2. **Individual Visual Types**: Create specific visuals

   - **Meeting Summary**: Professional overview images for stakeholders
   - **Action Item Boards**: Visual task management with priorities and owners
   - **Decision Trees**: Flowcharts showing meeting decisions and reasoning
   - **Infographics**: Statistical summaries with engagement metrics

3. **Visual Gallery**: Access via "Visuals" in navigation
   - Browse all visual assets across meetings
   - Organized by type (summaries, actions, decisions, infographics)
   - Download presentation-ready materials
   - Share visual reports with stakeholders

### Key Search Features

- **Semantic Understanding**: Search by meaning, not just exact words
- **Cross-Meeting Discovery**: Find related content across different meetings
- **Similarity Scoring**: See how relevant results are (percentage match)
- **Theme Analysis**: Discover patterns in action items, decisions, challenges, etc.
- **AI Recommendations**: Get suggestions for meeting optimization

### Translate Meeting Content

1. **Start Translation**: From any transcribed meeting

   - Click "Translate Content" button on meeting detail page
   - Select target language from 10+ supported low-resource languages
   - Choose content types to translate (transcript, summary, action items, decisions, topics)
   - Wait for GPT-4 translation (typically 1-3 minutes)

2. **Supported Languages**:

   - **Georgian** (ქართული) - `ka`
   - **Slovak** (Slovenčina) - `sk`
   - **Slovenian** (Slovenščina) - `sl`
   - **Latvian** (Latviešu) - `lv`
   - **Lithuanian** (Lietuvių) - `lt`
   - **Estonian** (Eesti) - `et`
   - **Bulgarian** (Български) - `bg`
   - **Croatian** (Hrvatski) - `hr`
   - **Albanian** (Shqip) - `sq`
   - **Macedonian** (Македонски) - `mk`

3. **View Translations**: Access translated content

   - Click "View Translations" to see all available languages
   - Browse translations by language or content type
   - View side-by-side with original content
   - Export translations as text files

4. **Search Translations**: Multi-language search capability

   - Use "Translations" in navigation for cross-language search
   - Filter by specific languages or search across all translations
   - Find content in native languages with context preservation
   - Business-appropriate translations maintaining professional tone

### Translation Features

- **Context-Aware Translation**: GPT-4 maintains business context and professional tone
- **Content Type Preservation**: Maintains formatting for action items, decisions, and topics
- **Speaker Attribution**: Preserves speaker labels and conversation flow in transcripts
- **Cultural Appropriateness**: Ensures business-appropriate language for each culture
- **Quality Assurance**: Low temperature settings for consistent, accurate translations

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
├── semantic_search.py    # Embeddings API + semantic search engine
├── visual_synthesis.py   # DALL-E 3 API + visual asset generation
├── translation_processor.py # GPT-4 translation for low-resource languages
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── meeting_detail.html
│   ├── search_results.html
│   ├── similar_meetings.html
│   ├── insights.html
│   ├── visual_detail.html
│   ├── meeting_visuals.html
│   ├── visual_gallery.html
│   ├── meeting_translations.html
│   ├── single_language_translation.html
│   ├── translation_search.html
│   └── translation_search_results.html
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
- **embeddings**: Vector embeddings for semantic search and similarity analysis
- **translations**: Multi-language translations with content type and language metadata
- **visual_assets**: DALL-E 3 generated images with metadata and prompts

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

## 📄 License

This project is developed for KIU Consulting's internal use.

---

**Note**: This system now includes ALL 4 PHASES COMPLETE + BONUS FEATURES:

- ✅ **Phase 1**: Audio Processing (Whisper API)
- ✅ **Phase 2**: Content Analysis (GPT-4 + Function Calling)
- ✅ **Phase 3**: Semantic Search (Embeddings API)
- ✅ **Phase 4**: Visual Synthesis (DALL-E 3 API)
- ✅ **BONUS**: Low Resource Language Translation Support (GPT-4)

**Complete AI Meeting Assistant** with all OpenAI APIs integrated, professional visual asset generation, and multi-language support for global accessibility.
