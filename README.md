# Transcription Processing with Pinecone and OpenAI Embeddings

This project processes transcription text files, converts them into embeddings using `OpenAI's API`, and stores them in a `Pinecone index`. It helps organize large volumes of text data for efficient search and retrieval based on semantic similarity.

## Overview

The script performs the following tasks:

1. **Reads Transcriptions**: It processes transcription files (in `.txt` format) stored in a specified folder.
2. **Splits Text**: Long text is split into smaller chunks for better processing and storage.
3. **Generates Embeddings**: Each chunk of text is embedded using `OpenAI's` embeddings model.
4. **Stores in Pinecone**: The embeddings are stored in a `Pinecone index` for efficient retrieval.
5. **Handles Index Management**: It checks if the `Pinecone index` exists and creates a new one if needed.
6. **Debug Mode**: The script has optional logging to track progress and debug information.

## Requirements

- Python 3.12+
- Required libraries:
  - `dotenv`
  - `pinecone-client`
  - `langchain-openai`
  - `langchain-text-splitters`
  
You can install the dependencies via:

```bash
pip install -r requirements.txt
```

## Configuration
Before running the script, make sure to create the following configuration files:

1. `.env` 

This file should contain your environment variables:
```
PINECONE_API_KEY=your_pinecone_api_key
OPENAI_API_KEY=your_openai_api_key
```

2. `config.json`

This JSON file should contain the settings for Pinecone and other parameters.

## Usage

### Running the Script

You can run the script by executing the following command:
```python
python pinecone_embeddings.py
```

This will:
1. Load the configuration from `config.json` and `.env`.
2. Create or retrieve the specified `Pinecone index`.
3. Process `.txt` transcription files from the folder specified in the config.
4. Split the text, generate embeddings, and store them in `Pinecone`.

### Debug Mode

If debug is set to true in `config.json`, the script will log detailed information about the processing of each transcription file. It will show:
1. The number of files processed.
2. The status of the Pinecone index.
3. The success or failure of embedding and storing each file.
   
## License
This project is licensed under the `MIT License` - see the [LICENSE](LICENSE) file for details.