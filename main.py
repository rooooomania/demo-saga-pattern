from flask import Flask
from flask_cors import CORS
from app.apis.event_api import event_bp
from app.apis.event_details_api import event_details_bp
from app.apis.venue_api import venue_bp
from app.apis.ticket_api import ticket_bp
from app.saga.saga_orchestrator import saga_bp
from app.demo.demo_endpoints import demo_bp

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(event_bp, url_prefix='/api/event')
    app.register_blueprint(event_details_bp, url_prefix='/api/event-details')
    app.register_blueprint(venue_bp, url_prefix='/api/venue')
    app.register_blueprint(ticket_bp, url_prefix='/api/ticket')
    app.register_blueprint(saga_bp, url_prefix='/api/saga')
    app.register_blueprint(demo_bp, url_prefix='/demo')
    
    @app.route('/')
    def health_check():
        return {'status': 'Saga Pattern Demo API is running', 'version': '1.0.0'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)