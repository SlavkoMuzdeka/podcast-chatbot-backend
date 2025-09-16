# Podcast Chatbot Backend

A robust backend service for a podcast chatbot application that enables users to interact with podcast content through natural language. The system leverages AI to provide intelligent responses based on podcast transcripts.

## 🚀 Features

- **User Authentication**: Secure JWT-based authentication system
- **Expert Management**: Create and manage podcast experts/personalities
- **Episode Management**: Upload and manage podcast episodes
- **AI-Powered Chat**: Interact with podcast content using natural language
- **Vector Search**: Semantic search powered by Pinecone for relevant content retrieval
- **RESTful API**: Well-documented endpoints for easy integration

## 🛠️ Tech Stack

- **Backend Framework**: Flask 3.1.1
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Database**: Pinecone for semantic search
- **AI/ML**: OpenAI's embeddings and language models
- **Authentication**: JWT (JSON Web Tokens)
- **API Documentation**: OpenAPI/Swagger (coming soon)

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** (recommended: 3.9 or later)
- **PostgreSQL** (version 13 or later recommended)
- **Pinecone account** (free tier available at [Pinecone.io](https://www.pinecone.io/))
- **OpenAI API key** (get it from [OpenAI Platform](https://platform.openai.com/))
- **pip** (Python package installer)
- **Git** (for version control)

## 🚀 Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/SlavkoMuzdeka/podcast-chatbot-backend.git
cd podcast-chatbot-backend
```

### 2. Set Up Python Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

With your virtual environment activated, install the required packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory.

### 5. Database Setup

1. Create a new PostgreSQL database:
   ```bash
   createdb podcast_chatbot
   ```

2. Initialize the database:
   ```bash
   flask db upgrade
   ```

### 6. Start the Application

```bash
python app.py
```

The application will start on `http://localhost:5000` by default.

### 7. Verify Installation

To verify everything is working correctly, you can call the health check endpoint:

```bash
curl http://localhost:5000/api/health
```

You should receive a response like:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-16T09:50:16.123456"
}
```

## 🔧 Common Issues and Troubleshooting

### Virtual Environment Not Activating
If you're having trouble activating the virtual environment:
- On Windows, try: `.\venv\Scripts\activate`
- Ensure you're in the project root directory
- If using PowerShell, you might need to change the execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Missing Dependencies
If you get import errors, ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Database Connection Issues
- Verify PostgreSQL is running
- Check your `DATABASE_URL` in the `.env` file
- Ensure the database user has the correct permissions

### Environment Variables Not Loading
- Ensure the `.env` file is in the root directory
- The file should be named exactly `.env` (not `.env.txt` or similar)
- Restart your terminal/IDE after creating the `.env` file

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.