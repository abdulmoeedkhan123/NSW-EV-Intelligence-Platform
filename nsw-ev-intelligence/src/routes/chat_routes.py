"""API routes for RAG-powered AI chat"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from src.services.rag_service import rag_pipeline

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    RAG chat endpoint for natural language queries about EV infrastructure
    
    Request body (JSON):
        - question (str, required): User's natural language question
        
    Returns:
        JSON response with AI-generated answer and source documents
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                "status": "error",
                "message": "Question is required"
            }), 400
        
        # Run RAG pipeline
        result = rag_pipeline(question, top_k=5)
        
        return jsonify({
            "status": "success",
            "answer": result['answer'],
            "sources": result['sources'][:3],  # Return top 3 sources
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": f"Chat processing error: {str(e)}"
        }), 500
