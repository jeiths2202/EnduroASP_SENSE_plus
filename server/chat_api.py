#!/usr/bin/env python3
"""
Chat API for Ollama integration
Handles multimodal chat requests and RAG document processing
"""

import os
import json
import base64
import requests
import time
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import mimetypes
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import BitNet service
try:
    from bitnet_service import bitnet_service
    BITNET_AVAILABLE = True
    logger.info("BitNet service imported successfully")
except ImportError as e:
    BITNET_AVAILABLE = False
    logger.warning(f"BitNet service not available: {e}")

# Import RAG service
try:
    from rag_service import get_rag_service
    RAG_AVAILABLE = True
    logger.info("RAG service imported successfully")
except ImportError as e:
    RAG_AVAILABLE = False
    logger.warning(f"RAG service not available: {e}")

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
    
    def call_bitnet(self, prompt, options=None):
        """Call BitNet B1.58 model"""
        try:
            if not BITNET_AVAILABLE:
                return {
                    'success': False,
                    'error': 'BitNet service not available'
                }
            
            if options is None:
                options = {
                    'temperature': 0.7,
                    'threads': 4,
                    'timeout': 30,
                    'conversational': True
                }
            
            result = bitnet_service.generate_response(prompt, options)
            
            return {
                'success': result.get('success', True),
                'response': result.get('response', ''),
                'model_info': result.get('model', 'BitNet B1.58 2B'),
                'inference_time': result.get('inference_time', 0),
                'tokens_per_second': result.get('tokens_per_second', 0),
                'mock': result.get('mock', False),
                'error': result.get('error')
            }
            
        except Exception as e:
            logger.error(f"BitNet call error: {e}")
            return {
                'success': False,
                'error': f'BitNet error: {str(e)}'
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
        """Search RAG documents using vector similarity"""
        try:
            if not RAG_AVAILABLE:
                logger.warning("RAG service not available, falling back to simple text search")
                return self._simple_text_search(query)
            
            # Use RAG service for vector search
            rag_service = get_rag_service()
            search_results = rag_service.search_documents(
                query=query,
                n_results=5,
                min_score=0.1
            )
            
            # Convert RAG results to expected format
            results = []
            for result in search_results:
                results.append({
                    'file': result['metadata'].get('source', 'unknown').split('/')[-1],
                    'path': result['metadata'].get('source', 'unknown'),
                    'snippet': result['content'][:500] + '...' if len(result['content']) > 500 else result['content'],
                    'similarity': result['similarity'],
                    'rank': result['rank']
                })
            
            return results
            
        except Exception as e:
            logger.error(f"RAG vector search error: {e}")
            # Fallback to simple text search
            return self._simple_text_search(query)
    
    def _simple_text_search(self, query):
        """Fallback simple text search in RAG directory"""
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
                                'snippet': content[:500] + '...' if len(content) > 500 else content,
                                'similarity': 0.5  # Default similarity for text search
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
                                'snippet': content[:500] + '...' if len(content) > 500 else content,
                                'similarity': 0.5  # Default similarity for text search
                            })
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
            
            return results[:5]  # Return top 5 results
            
        except Exception as e:
            logger.error(f"Simple text search error: {e}")
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
    """Get list of available models from Ollama and BitNet"""
    try:
        models = []
        
        # Add BitNet model first
        if BITNET_AVAILABLE:
            bitnet_info = bitnet_service.get_model_info()
            models.append({
                'name': bitnet_info['name'],
                'friendly_name': bitnet_info['friendly_name'],
                'size': int(bitnet_info['size'] * 1024 * 1024 * 1024),  # Convert GB to bytes
                'modified_at': '',
                'type': 'bitnet',
                'description': bitnet_info['description'],
                'available': bitnet_info['available']
            })
        
        # Get Ollama models
        try:
            response = requests.get(f'{OLLAMA_URL}/api/tags', timeout=10)
            if response.status_code == 200:
                data = response.json()
                
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
                        'modified_at': model.get('modified_at', ''),
                        'type': 'ollama',
                        'available': True
                    })
        except Exception as ollama_error:
            logger.warning(f"Failed to fetch Ollama models: {ollama_error}")
        
        return jsonify({'models': models})
        
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
        
        # Map frontend model names to backend models
        model_mapping = {
            'Gemma 2B': 'gemma:2b',
            'GPT-OSS 20B': 'gpt-oss:20b',
            'Qwen2.5 Coder 1.5B': 'qwen2.5-coder:1.5b',
            'BitNet B1.58 2B': 'bitnet-b1.58:2b'
        }
        backend_model = model_mapping.get(model, model)
        
        logger.info(f"Message: '{message}', Files count: {len(files)}, Use RAG: {use_rag}, Model: {model} -> {backend_model}")
        
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
                # Build more structured RAG context with better formatting
                rag_context = "\n\n=== 関連する参考資料 ===\n"
                for i, result in enumerate(rag_results[:3], 1):  # Limit to top 3 for context window
                    similarity_score = f" (関連度: {result.get('similarity', 0):.1%})" if result.get('similarity') else ""
                    rag_context += f"\n[資料{i}] {result['file']}{similarity_score}\n"
                    rag_context += f"内容: {result['snippet'][:300]}{'...' if len(result['snippet']) > 300 else ''}\n"
                
                rag_context += "\n=== 回答指示 ===\n"
                rag_context += "上記の参考資料を基に、正確で詳細な回答を提供してください。参考資料にない情報は推測せず、「参考資料には記載がありません」と明記してください。\n"
        
        # Build enhanced prompt with better structure
        enhanced_prompt = message
        
        if rag_context:
            enhanced_prompt = f"{rag_context}\n\n=== ユーザーの質問 ===\n{message}\n\n=== 回答 ==="
        
        if processed_files:
            files_info = "\n\n添付ファイル:\n"
            for file_info in processed_files:
                files_info += f"- {file_info['description']}\n"
                if file_info['type'] in ['text', 'markdown'] and 'content' in file_info:
                    files_info += f"  内容: {file_info['content'][:200]}...\n"
            enhanced_prompt += files_info
        
        # Route to appropriate model service
        if backend_model == 'bitnet-b1.58:2b':
            # Use BitNet service
            options = {
                'temperature': 0.7,
                'threads': 4,
                'timeout': 60,
                'conversational': True
            }
            result = chat_service.call_bitnet(enhanced_prompt, options)
        else:
            # Use Ollama service
            result = chat_service.call_ollama(
                prompt=enhanced_prompt,
                model=backend_model,
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
    """Upload document to RAG directory and auto-index"""
    try:
        data = request.get_json()
        
        if not data or 'file_data' not in data or 'filename' not in data:
            return jsonify({'error': 'file_data and filename required'}), 400
        
        processed = chat_service.process_file(
            data['file_data'], 
            data['filename']
        )
        
        # Auto-index the uploaded file if RAG is available
        auto_index = data.get('auto_index', True)
        indexing_result = None
        
        if auto_index and RAG_AVAILABLE and processed.get('success'):
            try:
                rag_service = get_rag_service()
                
                # Get file content based on type
                file_content = ""
                if processed.get('type') == 'text' and processed.get('content'):
                    file_content = processed['content']
                elif processed.get('type') == 'markdown' and processed.get('content'):
                    file_content = processed['content']
                
                if file_content:
                    # Add document to RAG service
                    chunks_added = rag_service.add_document(
                        content=file_content,
                        source=processed.get('path', data['filename']),
                        metadata={
                            'filename': data['filename'],
                            'type': processed.get('type', 'unknown'),
                            'uploaded_at': time.time(),
                            'auto_indexed': True
                        }
                    )
                    
                    indexing_result = {
                        'indexed': True,
                        'chunks_added': chunks_added,
                        'message': f'{chunks_added}個のチャンクが追加されました'
                    }
                else:
                    indexing_result = {
                        'indexed': False,
                        'message': 'ファイル形式がRAGインデックスに対応していません'
                    }
                    
            except Exception as e:
                logger.error(f"Auto-indexing failed: {e}")
                indexing_result = {
                    'indexed': False,
                    'error': str(e),
                    'message': 'インデックス処理中にエラーが発生しました'
                }
        
        return jsonify({
            'success': True,
            'file_info': processed,
            'indexing': indexing_result
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

@app.route('/api/rag/index', methods=['POST'])
def index_rag_documents():
    """Index documents in RAG directory into vector database"""
    if not RAG_AVAILABLE:
        return jsonify({'error': 'RAG service not available'}), 503
    
    try:
        data = request.get_json() or {}
        directory_path = data.get('directory', RAG_DIR)
        file_types = data.get('file_types', ['.txt', '.md', '.pdf', '.json'])
        
        rag_service = get_rag_service()
        
        # Index documents from directory
        results = rag_service.load_documents_from_directory(
            directory_path=directory_path,
            file_types=file_types
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f'Indexed {results["total_chunks"]} chunks from {len(results["processed_files"])} files'
        })
        
    except Exception as e:
        logger.error(f"RAG indexing error: {e}")
        return jsonify({'error': f'Indexing error: {str(e)}'}), 500

@app.route('/api/rag/search', methods=['POST'])
def search_rag_documents():
    """Search for relevant documents using RAG"""
    if not RAG_AVAILABLE:
        return jsonify({'error': 'RAG service not available'}), 503
    
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'query is required'}), 400
        
        query = data['query']
        n_results = data.get('n_results', 5)
        min_score = data.get('min_score', 0.0)
        
        rag_service = get_rag_service()
        
        # Search for relevant documents
        results = rag_service.search_documents(
            query=query,
            n_results=n_results,
            min_score=min_score
        )
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        return jsonify({'error': f'Search error: {str(e)}'}), 500

@app.route('/api/rag/status', methods=['GET'])
def rag_status():
    """Get RAG service status and information"""
    if not RAG_AVAILABLE:
        return jsonify({
            'available': False,
            'error': 'RAG service not available'
        }), 503
    
    try:
        rag_service = get_rag_service()
        
        # Get health check
        health = rag_service.health_check()
        
        # Get collection info
        info = rag_service.get_collection_info()
        
        return jsonify({
            'available': True,
            'health': health,
            'collection': info,
            'rag_directory': RAG_DIR
        })
        
    except Exception as e:
        logger.error(f"RAG status error: {e}")
        return jsonify({
            'available': False,
            'error': f'Status error: {str(e)}'
        }), 500

@app.route('/api/rag/clear', methods=['POST'])
def clear_rag_collection():
    """Clear all documents from RAG collection"""
    if not RAG_AVAILABLE:
        return jsonify({'error': 'RAG service not available'}), 503
    
    try:
        rag_service = get_rag_service()
        
        # Clear the collection
        success = rag_service.clear_collection()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'RAG collection cleared successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to clear collection'
            }), 500
        
    except Exception as e:
        logger.error(f"RAG clear error: {e}")
        return jsonify({'error': f'Clear error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.getenv('CHAT_API_PORT', 3006))
    app.run(host='0.0.0.0', port=port, debug=True)