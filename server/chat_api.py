#!/usr/bin/env python3
"""
Chat API for Ollama integration
Handles multimodal chat requests and RAG document processing
"""

import os
import json
import base64
import requests
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import mimetypes
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=['http://localhost:3005'], supports_credentials=True, allow_headers=['Content-Type'])  # Allow React dev server

# Configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:3014')
RAG_DIR = os.getenv('RAG_DIR', '/home/aspuser/app/ofasp-refactor/public/RAG')
UPLOAD_DIR = os.path.join(RAG_DIR, 'uploads')

# Create directories if they don't exist
os.makedirs(RAG_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatService:
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.rag_dir = Path(RAG_DIR)
        self.upload_dir = Path(UPLOAD_DIR)
    
    def call_ollama(self, prompt, model='gemma:2b', context=None, images=None):
        """Call Ollama API with multimodal support"""
        try:
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 500
                }
            }
            
            # Add context if provided
            if context:
                payload['context'] = context
            
            # Add images if provided (base64 encoded)
            if images:
                payload['images'] = images
            
            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'response': data.get('response', ''),
                'context': data.get('context'),
                'done': data.get('done', True)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            return {
                'success': False,
                'error': f'Ollama API error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def process_file(self, file_data, filename):
        """Process uploaded file and extract content"""
        try:
            # Save file to upload directory
            file_path = self.upload_dir / filename
            
            # Decode base64 file data
            file_bytes = base64.b64decode(file_data.split(',')[1] if ',' in file_data else file_data)
            
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            # Get file type
            mime_type, _ = mimetypes.guess_type(filename)
            
            # Process based on file type
            if mime_type and mime_type.startswith('image/'):
                return {
                    'type': 'image',
                    'path': str(file_path),
                    'base64': file_data,
                    'description': f'Image file: {filename}'
                }
            elif mime_type == 'text/plain' or filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return {
                    'type': 'text',
                    'path': str(file_path),
                    'content': content,
                    'description': f'Text file: {filename}'
                }
            elif filename.endswith('.md'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return {
                    'type': 'markdown',
                    'path': str(file_path),
                    'content': content,
                    'description': f'Markdown file: {filename}'
                }
            else:
                return {
                    'type': 'unknown',
                    'path': str(file_path),
                    'description': f'File: {filename} (type: {mime_type or "unknown"})'
                }
                
        except Exception as e:
            logger.error(f"File processing error: {e}")
            return {
                'type': 'error',
                'error': str(e),
                'description': f'Error processing file: {filename}'
            }
    
    def search_rag_documents(self, query):
        """Search RAG documents for relevant context"""
        try:
            results = []
            
            # Simple text search in RAG directory
            for file_path in self.rag_dir.rglob('*.txt'):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            results.append({
                                'file': file_path.name,
                                'path': str(file_path),
                                'snippet': content[:500] + '...' if len(content) > 500 else content
                            })
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
            
            # Search markdown files
            for file_path in self.rag_dir.rglob('*.md'):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            results.append({
                                'file': file_path.name,
                                'path': str(file_path),
                                'snippet': content[:500] + '...' if len(content) > 500 else content
                            })
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
            
            return results[:5]  # Return top 5 results
            
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return []

# Initialize service
chat_service = ChatService()

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'chat_api'})

@app.route('/api/ollama/health', methods=['GET'])
def ollama_health():
    """Check Ollama server health"""
    try:
        response = requests.get(f'{OLLAMA_URL}/api/tags', timeout=5)
        if response.status_code == 200:
            return jsonify({'status': 'ok', 'ollama': 'connected'})
        else:
            return jsonify({'status': 'error', 'ollama': 'disconnected'}), 503
    except Exception as e:
        return jsonify({'status': 'error', 'ollama': 'disconnected', 'error': str(e)}), 503

@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get list of available models from Ollama"""
    try:
        response = requests.get(f'{OLLAMA_URL}/api/tags', timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = []
            
            # Map Ollama model names to friendly names
            friendly_names = {
                'gemma:2b': 'Gemma 2B',
                'gpt-oss:20b': 'GPT-OSS 20B',
                'qwen2.5-coder:1.5b': 'Qwen2.5 Coder 1.5B'
            }
            
            for model in data.get('models', []):
                model_name = model.get('name', '')
                friendly_name = friendly_names.get(model_name, model_name)
                models.append({
                    'name': model_name,
                    'friendly_name': friendly_name,
                    'size': model.get('size', 0),
                    'modified_at': model.get('modified_at', '')
                })
            
            return jsonify({'models': models})
        else:
            return jsonify({'error': 'Failed to fetch models from Ollama'}), 503
    except Exception as e:
        logger.error(f"Models endpoint error: {e}")
        return jsonify({'error': f'Models error: {str(e)}'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with multimodal support"""
    try:
        logger.info("Chat endpoint called")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Raw request data: {request.get_data()}")
        
        data = request.get_json()
        
        if not data:
            logger.error("No data provided in request")
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info(f"Received data keys: {list(data.keys())}")
        logger.info(f"Full data: {data}")
        
        message = data.get('message', '').strip()
        files = data.get('files', [])
        use_rag = data.get('use_rag', True)
        model = data.get('model', 'gemma:2b')
        
        # Map frontend model names to Ollama model names
        model_mapping = {
            'Gemma 2B': 'gemma:2b',
            'GPT-OSS 20B': 'gpt-oss:20b',
            'Qwen2.5 Coder 1.5B': 'qwen2.5-coder:1.5b'
        }
        ollama_model = model_mapping.get(model, model)
        
        logger.info(f"Message: '{message}', Files count: {len(files)}, Use RAG: {use_rag}, Model: {model} -> {ollama_model}")
        
        if not message and not files:
            logger.error("Neither message nor files provided")
            return jsonify({'error': 'Message or files required'}), 400
        
        # Process uploaded files
        processed_files = []
        images = []
        
        for file_info in files:
            if 'data' in file_info and 'name' in file_info:
                processed = chat_service.process_file(
                    file_info['data'], 
                    file_info['name']
                )
                processed_files.append(processed)
                
                # If it's an image, add to images array for Ollama
                if processed['type'] == 'image':
                    images.append(processed['base64'])
        
        # Build context from RAG documents
        rag_context = ""
        rag_results = []
        if use_rag and message:
            rag_results = chat_service.search_rag_documents(message)
            if rag_results:
                rag_context = "\n\n参考資料:\n"
                for result in rag_results:
                    rag_context += f"- {result['file']}: {result['snippet']}\n"
        
        # Build enhanced prompt
        enhanced_prompt = message
        
        if rag_context:
            enhanced_prompt = f"{rag_context}\n\nユーザーの質問: {message}"
        
        if processed_files:
            files_info = "\n\n添付ファイル:\n"
            for file_info in processed_files:
                files_info += f"- {file_info['description']}\n"
                if file_info['type'] in ['text', 'markdown'] and 'content' in file_info:
                    files_info += f"  内容: {file_info['content'][:200]}...\n"
            enhanced_prompt += files_info
        
        # Call Ollama API
        result = chat_service.call_ollama(
            prompt=enhanced_prompt,
            model=ollama_model,
            images=images if images else None
        )
        
        if result['success']:
            return jsonify({
                'response': result['response'],
                'processed_files': processed_files,
                'rag_results': rag_results if use_rag else [],
                'context': result.get('context')
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        import traceback
        logger.error(f"Chat endpoint error: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/rag/upload', methods=['POST'])
def upload_rag_document():
    """Upload document to RAG directory"""
    try:
        data = request.get_json()
        
        if not data or 'file_data' not in data or 'filename' not in data:
            return jsonify({'error': 'file_data and filename required'}), 400
        
        processed = chat_service.process_file(
            data['file_data'], 
            data['filename']
        )
        
        return jsonify({
            'success': True,
            'file_info': processed
        })
        
    except Exception as e:
        logger.error(f"RAG upload error: {e}")
        return jsonify({'error': f'Upload error: {str(e)}'}), 500

@app.route('/api/rag/list', methods=['GET'])
def list_rag_documents():
    """List documents in RAG directory"""
    try:
        documents = []
        
        for file_path in chat_service.rag_dir.rglob('*'):
            if file_path.is_file():
                stat = file_path.stat()
                documents.append({
                    'name': file_path.name,
                    'path': str(file_path.relative_to(chat_service.rag_dir)),
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'type': mimetypes.guess_type(str(file_path))[0] or 'unknown'
                })
        
        return jsonify({
            'documents': sorted(documents, key=lambda x: x['modified'], reverse=True)
        })
        
    except Exception as e:
        logger.error(f"RAG list error: {e}")
        return jsonify({'error': f'List error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.getenv('CHAT_API_PORT', 3006))
    app.run(host='0.0.0.0', port=port, debug=True)