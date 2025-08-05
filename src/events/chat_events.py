# events/chat_events.py - Basic WebSocket Events for Chat System
from flask_socketio import emit, join_room, leave_room, disconnect
from datetime import datetime
import json

def register_chat_events(socketio):
    """Register WebSocket events for chat system"""
    
    @socketio.on('connect')
    def on_connect():
        """Handle client connection"""
        print(f"🔌 Client connected at {datetime.utcnow().isoformat()}")
        emit('status', {
            'message': 'Connected to Symplle Chat',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'connected'
        })
    
    @socketio.on('disconnect')
    def on_disconnect():
        """Handle client disconnection"""
        print(f"❌ Client disconnected at {datetime.utcnow().isoformat()}")
    
    @socketio.on('join_room')
    def on_join_room(data):
        """Join a chat room"""
        try:
            room_id = data.get('room_id')
            username = data.get('username', 'Anonymous')
            
            if not room_id:
                emit('error', {'message': 'Room ID is required'})
                return
            
            join_room(str(room_id))
            
            # Notify room members
            emit('user_joined', {
                'username': username,
                'room_id': room_id,
                'timestamp': datetime.utcnow().isoformat(),
                'message': f'{username} joined the room'
            }, room=str(room_id))
            
            # Confirm to user
            emit('room_joined', {
                'room_id': room_id,
                'status': 'joined',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            print(f"👥 User {username} joined room {room_id}")
            
        except Exception as e:
            print(f"❌ Error joining room: {e}")
            emit('error', {'message': f'Error joining room: {str(e)}'})
    
    @socketio.on('leave_room')
    def on_leave_room(data):
        """Leave a chat room"""
        try:
            room_id = data.get('room_id')
            username = data.get('username', 'Anonymous')
            
            if not room_id:
                emit('error', {'message': 'Room ID is required'})
                return
            
            leave_room(str(room_id))
            
            # Notify room members
            emit('user_left', {
                'username': username,
                'room_id': room_id,
                'timestamp': datetime.utcnow().isoformat(),
                'message': f'{username} left the room'
            }, room=str(room_id))
            
            # Confirm to user
            emit('room_left', {
                'room_id': room_id,
                'status': 'left',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            print(f"👋 User {username} left room {room_id}")
            
        except Exception as e:
            print(f"❌ Error leaving room: {e}")
            emit('error', {'message': f'Error leaving room: {str(e)}'})
    
    @socketio.on('send_message')
    def on_send_message(data):
        """Send a message to a room"""
        try:
            room_id = data.get('room_id')
            content = data.get('content', '').strip()
            username = data.get('username', 'Anonymous')
            message_type = data.get('type', 'text')
            
            if not room_id:
                emit('error', {'message': 'Room ID is required'})
                return
            
            if not content:
                emit('error', {'message': 'Message content is required'})
                return
            
            # Create message object
            message = {
                'id': f"msg_{datetime.utcnow().timestamp()}",
                'content': content,
                'username': username,
                'room_id': room_id,
                'type': message_type,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'sent'
            }
            
            # Send to all users in room
            emit('new_message', message, room=str(room_id))
            
            # Confirm to sender
            emit('message_sent', {
                'message_id': message['id'],
                'status': 'delivered',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            print(f"💬 Message sent by {username} to room {room_id}: {content[:50]}...")
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            emit('error', {'message': f'Error sending message: {str(e)}'})
    
    @socketio.on('typing_start')
    def on_typing_start(data):
        """Handle typing indicator start"""
        try:
            room_id = data.get('room_id')
            username = data.get('username', 'Anonymous')
            
            if not room_id:
                emit('error', {'message': 'Room ID is required'})
                return
            
            # Notify others in room (exclude sender)
            emit('user_typing', {
                'username': username,
                'room_id': room_id,
                'typing': True,
                'timestamp': datetime.utcnow().isoformat()
            }, room=str(room_id), include_self=False)
            
        except Exception as e:
            print(f"❌ Error handling typing start: {e}")
            emit('error', {'message': f'Error handling typing: {str(e)}'})
    
    @socketio.on('typing_stop')
    def on_typing_stop(data):
        """Handle typing indicator stop"""
        try:
            room_id = data.get('room_id')
            username = data.get('username', 'Anonymous')
            
            if not room_id:
                emit('error', {'message': 'Room ID is required'})
                return
            
            # Notify others in room (exclude sender)
            emit('user_typing', {
                'username': username,
                'room_id': room_id,
                'typing': False,
                'timestamp': datetime.utcnow().isoformat()
            }, room=str(room_id), include_self=False)
            
        except Exception as e:
            print(f"❌ Error handling typing stop: {e}")
            emit('error', {'message': f'Error handling typing: {str(e)}'})
    
    @socketio.on('ping')
    def on_ping():
        """Handle ping for connection health check"""
        emit('pong', {
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'alive'
        })
    
    @socketio.on('get_room_info')
    def on_get_room_info(data):
        """Get room information"""
        try:
            room_id = data.get('room_id')
            
            if not room_id:
                emit('error', {'message': 'Room ID is required'})
                return
            
            # Basic room info (will be enhanced when database models are ready)
            room_info = {
                'room_id': room_id,
                'name': f'Room {room_id}',
                'participants_count': 0,  # Will be calculated from database
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            emit('room_info', room_info)
            
        except Exception as e:
            print(f"❌ Error getting room info: {e}")
            emit('error', {'message': f'Error getting room info: {str(e)}'})
    
    print("✅ Chat WebSocket events registered successfully!")
    print("📋 Available events:")
    print("   • connect / disconnect")
    print("   • join_room / leave_room") 
    print("   • send_message")
    print("   • typing_start / typing_stop")
    print("   • ping / pong")
    print("   • get_room_info")