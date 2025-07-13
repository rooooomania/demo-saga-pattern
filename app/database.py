import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading

class SharedDatabase:
    """
    共有データベースのシミュレーション
    実際のアプリケーションでは、PostgreSQL、MySQL等の実際のデータベースを使用
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        self.events = {}
        self.event_details = {}
        self.venues = {}
        self.tickets = {}
        self.transactions = {}
    
    # Events table operations
    def create_event(self, event_data: Dict[str, Any]) -> str:
        with self.lock:
            event_id = str(uuid.uuid4())
            self.events[event_id] = {
                'id': event_id,
                'name': event_data.get('name'),
                'description': event_data.get('description'),
                'date': event_data.get('date'),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            return event_id
    
    def delete_event(self, event_id: str) -> bool:
        with self.lock:
            if event_id in self.events:
                del self.events[event_id]
                return True
            return False
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.events.get(event_id)
    
    def list_events(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.events.values())
    
    # Event Details table operations
    def create_event_details(self, event_id: str, details_data: Dict[str, Any]) -> str:
        with self.lock:
            details_id = str(uuid.uuid4())
            self.event_details[details_id] = {
                'id': details_id,
                'event_id': event_id,
                'detailed_description': details_data.get('detailed_description'),
                'duration': details_data.get('duration'),
                'category': details_data.get('category'),
                'requirements': details_data.get('requirements'),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            return details_id
    
    def delete_event_details(self, details_id: str) -> bool:
        with self.lock:
            if details_id in self.event_details:
                del self.event_details[details_id]
                return True
            return False
    
    def get_event_details(self, details_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.event_details.get(details_id)
    
    def list_event_details(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.event_details.values())
    
    # Venues table operations
    def create_venue(self, venue_data: Dict[str, Any]) -> str:
        with self.lock:
            venue_id = str(uuid.uuid4())
            self.venues[venue_id] = {
                'id': venue_id,
                'name': venue_data.get('name'),
                'address': venue_data.get('address'),
                'capacity': venue_data.get('capacity'),
                'facilities': venue_data.get('facilities'),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            return venue_id
    
    def delete_venue(self, venue_id: str) -> bool:
        with self.lock:
            if venue_id in self.venues:
                del self.venues[venue_id]
                return True
            return False
    
    def get_venue(self, venue_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.venues.get(venue_id)
    
    def list_venues(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.venues.values())
    
    # Tickets table operations  
    def create_ticket(self, ticket_data: Dict[str, Any]) -> str:
        with self.lock:
            ticket_id = str(uuid.uuid4())
            self.tickets[ticket_id] = {
                'id': ticket_id,
                'event_id': ticket_data.get('event_id'),
                'venue_id': ticket_data.get('venue_id'),
                'ticket_type': ticket_data.get('ticket_type'),
                'price': ticket_data.get('price'),
                'quantity': ticket_data.get('quantity'),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            return ticket_id
    
    def delete_ticket(self, ticket_id: str) -> bool:
        with self.lock:
            if ticket_id in self.tickets:
                del self.tickets[ticket_id]
                return True
            return False
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.tickets.get(ticket_id)
    
    def list_tickets(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.tickets.values())
    
    # Transaction management for Saga
    def create_transaction(self, transaction_data: Dict[str, Any]) -> str:
        with self.lock:
            transaction_id = str(uuid.uuid4())
            self.transactions[transaction_id] = {
                'id': transaction_id,
                'status': transaction_data.get('status', 'pending'),
                'steps': transaction_data.get('steps', []),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'metadata': transaction_data.get('metadata', {})
            }
            return transaction_id
    
    def update_transaction(self, transaction_id: str, updates: Dict[str, Any]) -> bool:
        with self.lock:
            if transaction_id in self.transactions:
                self.transactions[transaction_id].update(updates)
                self.transactions[transaction_id]['updated_at'] = datetime.now().isoformat()
                return True
            return False
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.transactions.get(transaction_id)
    
    def list_transactions(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.transactions.values())
    
    def get_database_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'events_count': len(self.events),
                'event_details_count': len(self.event_details),
                'venues_count': len(self.venues), 
                'tickets_count': len(self.tickets),
                'transactions_count': len(self.transactions),
                'total_records': len(self.events) + len(self.event_details) + len(self.venues) + len(self.tickets)
            }

# Global database instance (シングルトンパターン)
db = SharedDatabase()