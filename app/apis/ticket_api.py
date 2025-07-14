from flask import Blueprint, request, jsonify
from app.database import db

ticket_bp = Blueprint('ticket', __name__)

@ticket_bp.route('/register', methods=['POST'])
def register_ticket():
    """
    チケット券面登録API
    チケットの券面情報を登録する
    """
    try:
        data = request.get_json()
        
        # 入力検証
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['event_id', 'venue_id', 'ticket_type', 'price', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # 関連するイベントと会場が存在するか確認
        event = db.get_event(data['event_id'])
        if not event:
            return jsonify({'error': 'Related event not found'}), 400
            
        venue = db.get_venue(data['venue_id'])
        if not venue:
            return jsonify({'error': 'Related venue not found'}), 400
        
        # Saga テスト用: 失敗をシミュレートする場合
        if data.get('simulate_failure'):
            return jsonify({'error': 'Simulated failure in ticket registration'}), 500
        
        # チケット作成
        ticket_id = db.create_ticket(data)
        
        return jsonify({
            'success': True,
            'ticket_id': ticket_id,
            'event_id': data['event_id'],
            'venue_id': data['venue_id'],
            'message': 'Ticket registered successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ticket_bp.route('/rollback/<ticket_id>', methods=['DELETE'])
def rollback_ticket(ticket_id):
    """
    チケット券面ロールバック
    Saga失敗時の補償トランザクション
    """
    try:
        success = db.delete_ticket(ticket_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Ticket {ticket_id} rolled back successfully'
            }), 200
        else:
            return jsonify({'error': 'Ticket not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ticket_bp.route('/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """
    チケット情報取得
    """
    try:
        ticket = db.get_ticket(ticket_id)
        
        if ticket:
            return jsonify(ticket), 200
        else:
            return jsonify({'error': 'Ticket not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ticket_bp.route('/list', methods=['GET'])
def list_tickets():
    """
    全チケット一覧取得
    """
    try:
        tickets = db.list_tickets()
        return jsonify({'tickets': tickets}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ticket_bp.route('/health', methods=['GET'])
def health():
    """
    APIヘルスチェック
    """
    return jsonify({'status': 'Ticket API is healthy'}), 200