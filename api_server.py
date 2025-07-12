from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import os
import logging
from datetime import datetime
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
@jwt_required()
@limiter.limit("10 per minute")
def serve_web_app():
    """Serve the web app"""
    try:
        app_path = 'mobile-app/public/app.html'
        if os.path.exists(app_path):
            return send_file(app_path)
        else:
            return jsonify({'error': 'Web app not found'}), 404
            
    except Exception as e:
        logger.error(f"Error serving web app: {e}")
        return jsonify({'error': 'Failed to serve web app'}), 500

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