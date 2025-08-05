# config/socketio_config.py - Basic SocketIO Configuration for Chat System

def create_socketio(app):
    """Create and configure SocketIO instance for chat system"""
    
    try:
        from flask_socketio import SocketIO
    except ImportError:
        print("⚠️ Flask-SocketIO not available")
        return None
    
    # Basic SocketIO configuration
    socketio = SocketIO(
        app,
        # CORS settings
        cors_allowed_origins="*",  # Allow all origins for development
        
        # Async mode
        async_mode='eventlet',  # Use eventlet for async operations
        
        # Logging
        logger=True,            # Enable SocketIO logging
        engineio_logger=True,   # Enable Engine.IO logging
        
        # Connection settings
        ping_timeout=60,        # Timeout for ping/pong (seconds)
        ping_interval=25,       # Interval between pings (seconds)
        
        # Transport settings
        transports=['websocket', 'polling'],  # Allow both WebSocket and polling
        
        # Namespace settings
        namespace=None,         # Use default namespace
        
        # Additional settings
        always_connect=False,   # Don't always connect on page load
        cookie=None,           # No custom cookie handling
        manage_session=True,   # Let SocketIO manage sessions
        
        # JSON handling
        json=None,             # Use default JSON encoder/decoder
        
        # Connection handling
        allow_upgrades=True,   # Allow transport upgrades
        http_compression=True, # Enable HTTP compression
        compression_threshold=1024,  # Compress messages > 1KB
        
        # Error handling
        engineio_logger_level='INFO'  # Set logging level
    )
    
    print("✅ SocketIO configured successfully!")
    print("📋 Configuration:")
    print("   • CORS: All origins allowed")
    print("   • Async mode: eventlet")
    print("   • Transports: WebSocket + polling")
    print("   • Ping timeout: 60s")
    print("   • Ping interval: 25s")
    print("   • Compression: Enabled")
    print("   • Logging: Enabled")
    
    return socketio