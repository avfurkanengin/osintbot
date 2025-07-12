from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import json
from database import DatabaseManager
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for mobile app
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')  # Change this in production!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)  # Token expires in 7 days
jwt = JWTManager(app)

# Initialize database
db = DatabaseManager()

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'success': False, 'message': 'Missing username or password'}), 400
    
    user = db.get_user_by_username(data['username'])
    if not user or not db.verify_password(user['password_hash'], data['password']):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    # Create token with 7-day expiration
    access_token = create_access_token(identity=user['username'])
    return jsonify({
        'success': True,
        'token': access_token,
        'user': {
            'username': user['username'],
            'role': user['role']
        }
    }), 200

@app.route('/api/health', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/posts', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def get_posts():
    """Get posts with optional filtering"""
    try:
        # Get query parameters
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Validate parameters
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 1
            
        posts = db.get_posts(status=status, limit=limit, offset=offset)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'count': len(posts),
            'filters': {
                'status': status,
                'limit': limit,
                'offset': offset
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/<int:post_id>', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def get_post(post_id: int):
    """Get a specific post by ID"""
    try:
        posts = db.get_posts()
        post = next((p for p in posts if p['id'] == post_id), None)
        
        if not post:
            return jsonify({
                'success': False,
                'error': 'Post not found'
            }), 404
            
        return jsonify({
            'success': True,
            'post': post
        })
        
    except Exception as e:
        logger.error(f"Error getting post {post_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/<int:post_id>/action', methods=['POST'])
@jwt_required()
@limiter.limit("50 per minute")
def post_action(post_id: int) -> Union[Response, tuple[Response, int]]:
    """Perform an action on a post"""
    try:
        data = request.get_json()
        action_type = data.get('action_type')
        notes = data.get('notes', '')
        
        if not action_type:
            return jsonify({
                'success': False,
                'error': 'action_type is required'
            }), 400
            
        valid_actions = ['post_twitter', 'delete', 'archive', 'approve', 'reject']
        if action_type not in valid_actions:
            return jsonify({
                'success': False,
                'error': f'Invalid action. Must be one of: {valid_actions}'
            }), 400
        
        # Update post status based on action
        status_map = {
            'post_twitter': 'posted',
            'delete': 'deleted',
            'archive': 'archived',
            'approve': 'approved',
            'reject': 'rejected'
        }
        
        new_status = status_map.get(action_type, 'processed')
        
        # For Twitter posting, include the Twitter URL if provided
        kwargs = {}
        if action_type == 'post_twitter' and data.get('twitter_url'):
            kwargs['twitter_url'] = data['twitter_url']
        
        # Update post status
        success = db.update_post_status(post_id, new_status, **kwargs)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Post not found or update failed'
            }), 404
        
        # Record user action
        db.add_user_action(post_id, action_type, notes)
        
        return jsonify({
            'success': True,
            'message': f'Action {action_type} completed successfully',
            'post_id': post_id,
            'new_status': new_status
        })
        
    except Exception as e:
        logger.error(f"Error performing action on post {post_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/batch-action', methods=['POST'])
@jwt_required()
@limiter.limit("50 per minute")
def batch_action():
    """Perform batch actions on multiple posts"""
    try:
        data = request.get_json()
        post_ids = data.get('post_ids', [])
        action_type = data.get('action_type')
        notes = data.get('notes', '')
        
        if not post_ids or not action_type:
            return jsonify({
                'success': False,
                'error': 'post_ids and action_type are required'
            }), 400
        
        results = []
        for post_id in post_ids:
            try:
                # Update post status
                status_map = {
                    'delete': 'deleted',
                    'archive': 'archived',
                    'approve': 'approved',
                    'reject': 'rejected'
                }
                
                new_status = status_map.get(action_type, 'processed')
                success = db.update_post_status(post_id, new_status)
                
                if success:
                    db.add_user_action(post_id, action_type, notes)
                    results.append({'post_id': post_id, 'success': True})
                else:
                    results.append({'post_id': post_id, 'success': False, 'error': 'Update failed'})
                    
            except Exception as e:
                results.append({'post_id': post_id, 'success': False, 'error': str(e)})
        
        successful_count = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'message': f'Batch action completed: {successful_count}/{len(post_ids)} successful',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error performing batch action: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analytics', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def get_analytics():
    """Get analytics data"""
    try:
        days = int(request.args.get('days', 7))
        if days > 30:
            days = 30
        if days < 1:
            days = 1
            
        analytics = db.get_analytics(days=days)
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def get_stats():
    """Get quick stats for dashboard"""
    try:
        # Get counts by status
        all_posts = db.get_posts(limit=1000)  # Get more posts for accurate counts
        
        # Calculate counts
        total_posts = len(all_posts)
        pending_posts = len([p for p in all_posts if p['status'] == 'pending'])
        posted_count = len([p for p in all_posts if p['status'] == 'posted'])
        deleted_count = len([p for p in all_posts if p['status'] == 'deleted'])
        archived_count = len([p for p in all_posts if p['status'] == 'archived'])
        
        # Calculate rates
        if total_posts > 0:
            post_rate = round((posted_count / total_posts) * 100, 1)
            delete_rate = round((deleted_count / total_posts) * 100, 1)
        else:
            post_rate = 0.0
            delete_rate = 0.0
        
        stats = {
            'total_posts': total_posts,
            'pending_posts': pending_posts,
            'posted_count': posted_count,
            'deleted_count': deleted_count,
            'archived_count': archived_count,
            'post_rate': post_rate,
            'delete_rate': delete_rate,
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/media/<path:filename>', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def serve_media(filename):
    """Serve media files"""
    try:
        # Security check - only allow files in media directory
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid file path'}), 400
        
        # Check if filename already includes media/ prefix
        if filename.startswith('media/'):
            media_path = filename
        else:
            media_path = os.path.join('media', filename)
            
        if os.path.exists(media_path):
            return send_file(media_path)
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        logger.error(f"Error serving media {filename}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logo', methods=['GET'])
@jwt_required()
@limiter.limit("10 per minute")
def serve_logo():
    """Serve the logo file"""
    try:
        logo_path = 'media/logo.jpeg'
        if os.path.exists(logo_path):
            return send_file(logo_path)
        else:
            return jsonify({'error': 'Logo not found'}), 404
            
    except Exception as e:
        logger.error(f"Error serving logo: {e}")
        return jsonify({'error': 'Failed to serve logo'}), 500

@app.route('/api/header', methods=['GET'])
@jwt_required()
@limiter.limit("10 per minute")
def serve_header():
    """Serve the header image file"""
    try:
        header_path = 'media/header.JPG'
        if os.path.exists(header_path):
            return send_file(header_path)
        else:
            return jsonify({'error': 'Header image not found'}), 404
            
    except Exception as e:
        logger.error(f"Error serving header: {e}")
        return jsonify({'error': 'Failed to serve header'}), 500

@app.route('/', methods=['GET'])
@limiter.limit("10 per minute")
def serve_web_app():
    """Serve the unified web app that handles both login and dashboard"""
    try:
        unified_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>the Pulse - Geopolitics</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background-color: #121212;
            color: #ffffff;
            overflow-x: hidden;
        }
        
        /* Login Screen Styles */
        .login-screen {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        
        @media (min-width: 768px) {
            .login-screen {
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                padding: 20px;
            }
            
            .login-container {
                max-width: 414px;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                overflow: hidden;
                background: #121212;
            }
        }
        
        .login-container {
            width: 100%;
            max-width: 400px;
            background: #121212;
            padding: 40px 30px;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .login-title {
            color: #ffffff;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        
        .login-subtitle {
            color: #cccccc;
            font-size: 16px;
            font-weight: 400;
        }
        
        .form-group {
            margin-bottom: 24px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: 500;
            color: #ffffff;
        }
        
        .form-input {
            width: 100%;
            padding: 16px;
            border: 1px solid #333333;
            border-radius: 8px;
            font-size: 16px;
            background: #1e1e1e;
            color: #ffffff;
            transition: border-color 0.3s;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #2196F3;
        }
        
        .login-button {
            width: 100%;
            padding: 16px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            margin-top: 8px;
        }
        
        .login-button:hover {
            background: #1976D2;
        }
        
        .login-button:disabled {
            background: #333333;
            cursor: not-allowed;
        }
        
        .message {
            margin-top: 16px;
            padding: 12px;
            border-radius: 6px;
            text-align: center;
            font-size: 14px;
        }
        
        .message.error {
            background: #2d1b1b;
            color: #ff5252;
            border-left: 4px solid #f44336;
        }
        
        .message.success {
            background: #1b2d1b;
            color: #4caf50;
            border-left: 4px solid #4caf50;
        }
        
        /* Dashboard Styles */
        .dashboard-screen {
            display: none;
            width: 100%;
            height: 100vh;
        }
        
        .loading-screen {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            flex-direction: column;
        }
        
        .loading-spinner {
            border: 3px solid #333333;
            border-top: 3px solid #2196F3;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <!-- Loading Screen -->
    <div id="loadingScreen" class="loading-screen">
        <div class="loading-spinner"></div>
        <p>Loading...</p>
    </div>
    
    <!-- Login Screen -->
    <div id="loginScreen" class="login-screen hidden">
        <div class="login-container">
            <div class="login-header">
                <h1 class="login-title">the Pulse</h1>
                <p class="login-subtitle">Geopolitics</p>
            </div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label class="form-label" for="username">ID</label>
                    <input class="form-input" type="text" id="username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="password">Password</label>
                    <input class="form-input" type="password" id="password" name="password" required>
                </div>
                
                <button class="login-button" type="submit">Login</button>
            </form>
            
            <div id="message" class="message" style="display: none;"></div>
        </div>
    </div>
    
    <!-- Dashboard Screen -->
    <div id="dashboardScreen" class="dashboard-screen">
        <iframe id="dashboardFrame" src="" width="100%" height="100%" frameborder="0"></iframe>
    </div>

    <script>
        // Check authentication status on page load
        window.addEventListener('load', function() {
            checkAuthAndLoadContent();
        });
        
        async function checkAuthAndLoadContent() {
            const token = localStorage.getItem('jwt_token');
            
            if (!token) {
                // No token, show login screen
                showLoginScreen();
                return;
            }
            
            try {
                // Verify token with server
                const response = await fetch('/api/health', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    // Token is valid, load dashboard
                    loadDashboard();
                } else {
                    // Token is invalid, remove it and show login
                    localStorage.removeItem('jwt_token');
                    localStorage.removeItem('user_info');
                    showLoginScreen();
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                showLoginScreen();
            }
        }
        
        function showLoginScreen() {
            document.getElementById('loadingScreen').classList.add('hidden');
            document.getElementById('loginScreen').classList.remove('hidden');
            document.getElementById('dashboardScreen').classList.add('hidden');
        }
        
        function loadDashboard() {
            document.getElementById('loadingScreen').classList.add('hidden');
            document.getElementById('loginScreen').classList.add('hidden');
            document.getElementById('dashboardScreen').classList.remove('hidden');
            
            // Load the dashboard content
            fetch('/dashboard')
                .then(response => response.text())
                .then(html => {
                    document.getElementById('dashboardScreen').innerHTML = html;
                })
                .catch(error => {
                    console.error('Failed to load dashboard:', error);
                    showLoginScreen();
                });
        }
        
        // Handle login form submission
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const messageDiv = document.getElementById('message');
            const submitButton = document.querySelector('.login-button');
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.textContent = 'Logging in...';
            messageDiv.style.display = 'none';
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    // Store the JWT token
                    localStorage.setItem('jwt_token', data.token);
                    localStorage.setItem('user_info', JSON.stringify(data.user));
                    
                    // Show success message
                    messageDiv.textContent = 'Login successful! Loading dashboard...';
                    messageDiv.className = 'message success';
                    messageDiv.style.display = 'block';
                    
                    // Load dashboard
                    setTimeout(() => {
                        loadDashboard();
                    }, 1000);
                } else {
                    // Show error message
                    messageDiv.textContent = data.message || 'Login failed';
                    messageDiv.className = 'message error';
                    messageDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Login error:', error);
                messageDiv.textContent = 'Network error. Please try again.';
                messageDiv.className = 'message error';
                messageDiv.style.display = 'block';
            } finally {
                // Reset button
                submitButton.disabled = false;
                submitButton.textContent = 'Login';
            }
        });
    </script>
</body>
</html>
        '''
        from flask import Response
        return Response(unified_html, mimetype='text/html')
            
    except Exception as e:
        logger.error(f"Error serving web app: {e}")
        return jsonify({'error': 'Failed to serve web app'}), 500

@app.route('/dashboard', methods=['GET'])
@jwt_required()
@limiter.limit("10 per minute")
def serve_dashboard():
    """Serve the dashboard content"""
    try:
        app_path = 'mobile-app/public/app.html'
        if os.path.exists(app_path):
            return send_file(app_path)
        else:
            return jsonify({'error': 'Dashboard not found'}), 404
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        return jsonify({'error': 'Failed to serve dashboard'}), 500

@app.route('/api/cleanup', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def cleanup_posts():
    """Clean up old posts"""
    try:
        data = request.get_json() or {}
        days = data.get('days', 30)
        
        if days < 7:
            days = 7  # Minimum 7 days retention
            
        archived_count = db.cleanup_old_posts(days=days)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {archived_count} old posts',
            'archived_count': archived_count
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up posts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug) 