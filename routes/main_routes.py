"""
Main page routes
"""
from flask import render_template, redirect, url_for, request
from werkzeug.utils import secure_filename
import os
from config import Config

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def register_main_routes(app, video_processor):
    """
    Register main application routes
    
    Args:
        app: Flask application instance
        video_processor: VideoProcessor instance
    """
    
    @app.route('/')
    def home():
        return render_template('index.html', 
                             GRID_ROWS=Config.GRID_ROWS, 
                             GRID_COLS=Config.GRID_COLS)
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        # Check if a file was submitted
        if 'video' not in request.files:
            return redirect(request.url)
        
        file = request.files['video']
        
        # If user submits empty form
        if file.filename == '':
            return redirect(request.url)
        
        # If valid file and allowed extension
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Remove old uploaded files to save space
            for old_file in os.listdir(app.config['UPLOAD_FOLDER']):
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_file)
                if os.path.isfile(old_path):
                    os.unlink(old_path)
            
            # Save the new file
            file.save(file_path)
            
            # Set the video source
            video_processor.set_video_source(use_webcam=False, video_path=file_path)
            
            return redirect(url_for('home'))
        
        return redirect(request.url)
    
    @app.route('/use_webcam')
    def use_webcam():
        # Switch to webcam mode
        video_processor.set_video_source(use_webcam=True)
        
        return redirect(url_for('home'))