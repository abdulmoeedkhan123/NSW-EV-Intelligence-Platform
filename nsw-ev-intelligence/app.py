"""
NSW EV Intelligence Platform - Clean Modular Architecture
Main Flask application with RAG-powered chat and station intelligence
"""
from flask import Flask, render_template
from flask_cors import CORS
from src.routes.query_routes import query_bp
from src.routes.chat_routes import chat_bp
from src.routes.health_routes import health_bp

def create_app():
    """Application factory pattern for creating Flask app"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Enable CORS for all routes
    CORS(app)
    
    # Register blueprints (modular routes)
    app.register_blueprint(query_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)
    
    @app.route('/')
    def index():
        """Main web interface"""
        return render_template('index.html')
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    print("🚀 Starting NSW EV Intelligence Platform...")
    print("📍 Station Intelligence: /query")
    print("💬 AI Chat (RAG): /chat")
    print("❤️  Health Check: /health")
    app.run(host='0.0.0.0', port=8000, debug=False)
