# models/chat.py - Basic Chat System Models
import sys
import os
from datetime import datetime
from enum import Enum

# Add parent directory to path to access src.models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import database using same pattern as existing code
try:
    from src.models import db
except ImportError:
    try:
        from models import db
    except ImportError:
        print("⚠️ Database not found - chat models will not work")
        db = None

# Only define models if database is available
if db:
    
    class RoomType(Enum):
        """Types of chat rooms"""
        DIRECT = "direct"      # 1:1 conversation
        GROUP = "group"        # Group chat
        CHANNEL = "channel"    # Public channel
    
    class MessageType(Enum):
        """Types of messages"""
        TEXT = "text"
        IMAGE = "image"
        FILE = "file"
        SYSTEM = "system"
    
    class MessageStatus(Enum):
        """Message delivery status"""
        SENT = "sent"
        DELIVERED = "delivered"
        READ = "read"
        FAILED = "failed"
    
    class ChatRoom(db.Model):
        """Chat room/conversation model"""
        __tablename__ = 'chat_rooms'
        
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=True)  # Null for direct chats
        description = db.Column(db.Text, nullable=True)
        room_type = db.Column(db.Enum(RoomType), nullable=False, default=RoomType.GROUP)
        created_by = db.Column(db.Integer, nullable=False)  # User ID who created
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        is_active = db.Column(db.Boolean, default=True)
        
        # Settings
        is_public = db.Column(db.Boolean, default=False)
        max_participants = db.Column(db.Integer, default=100)
        
        # Relationships
        messages = db.relationship('ChatMessage', backref='room', lazy='dynamic', cascade='all, delete-orphan')
        participants = db.relationship('ChatParticipant', backref='room', lazy='dynamic', cascade='all, delete-orphan')
        
        def to_dict(self):
            """Convert to dictionary"""
            return {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'room_type': self.room_type.value if self.room_type else None,
                'created_by': self.created_by,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'is_active': self.is_active,
                'is_public': self.is_public,
                'max_participants': self.max_participants,
                'participants_count': self.participants.count()
            }
        
        def __repr__(self):
            return f'<ChatRoom {self.id}: {self.name or "Direct Chat"}>'
    
    class ChatParticipant(db.Model):
        """Chat room participants"""
        __tablename__ = 'chat_participants'
        
        id = db.Column(db.Integer, primary_key=True)
        room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
        user_id = db.Column(db.Integer, nullable=False)  # Reference to User
        joined_at = db.Column(db.DateTime, default=datetime.utcnow)
        left_at = db.Column(db.DateTime, nullable=True)
        is_active = db.Column(db.Boolean, default=True)
        
        # Participant settings
        is_admin = db.Column(db.Boolean, default=False)
        is_muted = db.Column(db.Boolean, default=False)
        notifications_enabled = db.Column(db.Boolean, default=True)
        
        # Unique constraint
        __table_args__ = (db.UniqueConstraint('room_id', 'user_id', name='unique_room_participant'),)
        
        def to_dict(self):
            """Convert to dictionary"""
            return {
                'id': self.id,
                'room_id': self.room_id,
                'user_id': self.user_id,
                'joined_at': self.joined_at.isoformat() if self.joined_at else None,
                'left_at': self.left_at.isoformat() if self.left_at else None,
                'is_active': self.is_active,
                'is_admin': self.is_admin,
                'is_muted': self.is_muted,
                'notifications_enabled': self.notifications_enabled
            }
        
        def __repr__(self):
            return f'<ChatParticipant room:{self.room_id} user:{self.user_id}>'
    
    class ChatMessage(db.Model):
        """Chat messages"""
        __tablename__ = 'chat_messages'
        
        id = db.Column(db.Integer, primary_key=True)
        room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
        sender_id = db.Column(db.Integer, nullable=False)  # Reference to User
        content = db.Column(db.Text, nullable=False)
        message_type = db.Column(db.Enum(MessageType), default=MessageType.TEXT)
        
        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        deleted_at = db.Column(db.DateTime, nullable=True)
        
        # Message metadata
        file_url = db.Column(db.String(500), nullable=True)  # For file/image messages
        file_name = db.Column(db.String(255), nullable=True)
        file_size = db.Column(db.Integer, nullable=True)
        
        # Reply/thread support
        reply_to_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=True)
        thread_id = db.Column(db.Integer, nullable=True)
        
        # Status and flags
        is_edited = db.Column(db.Boolean, default=False)
        is_deleted = db.Column(db.Boolean, default=False)
        is_pinned = db.Column(db.Boolean, default=False)
        
        # Relationships
        replies = db.relationship('ChatMessage', backref=db.backref('parent_message', remote_side=[id]), lazy='dynamic')
        statuses = db.relationship('MessageStatus', backref='message', lazy='dynamic', cascade='all, delete-orphan')
        
        def to_dict(self):
            """Convert to dictionary"""
            return {
                'id': self.id,
                'room_id': self.room_id,
                'sender_id': self.sender_id,
                'content': self.content,
                'message_type': self.message_type.value if self.message_type else None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
                'file_url': self.file_url,
                'file_name': self.file_name,
                'file_size': self.file_size,
                'reply_to_id': self.reply_to_id,
                'thread_id': self.thread_id,
                'is_edited': self.is_edited,
                'is_deleted': self.is_deleted,
                'is_pinned': self.is_pinned
            }
        
        def __repr__(self):
            return f'<ChatMessage {self.id} in room {self.room_id}>'
    
    class MessageStatus(db.Model):
        """Message delivery/read status per user"""
        __tablename__ = 'message_statuses'
        
        id = db.Column(db.Integer, primary_key=True)
        message_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=False)
        user_id = db.Column(db.Integer, nullable=False)  # Reference to User
        status = db.Column(db.Enum(MessageStatus), nullable=False)
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Unique constraint
        __table_args__ = (db.UniqueConstraint('message_id', 'user_id', name='unique_message_user_status'),)
        
        def to_dict(self):
            """Convert to dictionary"""
            return {
                'id': self.id,
                'message_id': self.message_id,
                'user_id': self.user_id,
                'status': self.status.value if self.status else None,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None
            }
        
        def __repr__(self):
            return f'<MessageStatus msg:{self.message_id} user:{self.user_id} status:{self.status}>'
    
    class TypingStatus(db.Model):
        """Typing indicators"""
        __tablename__ = 'typing_statuses'
        
        id = db.Column(db.Integer, primary_key=True)
        room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
        user_id = db.Column(db.Integer, nullable=False)  # Reference to User
        is_typing = db.Column(db.Boolean, default=True)
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Unique constraint
        __table_args__ = (db.UniqueConstraint('room_id', 'user_id', name='unique_room_user_typing'),)
        
        def to_dict(self):
            """Convert to dictionary"""
            return {
                'id': self.id,
                'room_id': self.room_id,
                'user_id': self.user_id,
                'is_typing': self.is_typing,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None
            }
        
        def __repr__(self):
            return f'<TypingStatus room:{self.room_id} user:{self.user_id} typing:{self.is_typing}>'
    
    print("✅ Chat models defined successfully!")
    print("📋 Models available:")
    print("   • ChatRoom - Chat rooms/conversations")
    print("   • ChatParticipant - Room participants")
    print("   • ChatMessage - Messages")
    print("   • MessageStatus - Delivery status")
    print("   • TypingStatus - Typing indicators")

else:
    # If no database, create placeholder classes
    class ChatRoom:
        pass
    
    class ChatParticipant:
        pass
        
    class ChatMessage:
        pass
        
    class MessageStatus:
        pass
        
    class TypingStatus:
        pass
    
    print("⚠️ Chat models not available - database not found")