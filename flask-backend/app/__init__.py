
from flask import Flask, current_app, request, render_template

from flask_talisman import Talisman



from .config import Config

from flask_cors import CORS

def create_app():
  app = Flask(__name__)
  app.config.from_object(Config)
  app.config['MAX_CONTENT_LENGTH'] = 6000 * 1024 * 1024

  CORS(app, supports_credentials=True, origins=[
    "http://localhost:4200",   # Angular Dev Server
    "https://tauri.localhost", # Tauri Windows Prod
    "asset://localhost",       # Tauri Mac Prod (v1)
    "tauri://localhost"        # Tauri Mac Prod (v2)
  ])
  Talisman(app,
           force_https=False,
           strict_transport_security=False,
           content_security_policy={
             'default-src': "'self'",
             'script-src': [
               "'self'",
               "'unsafe-inline'",
               "https://cdnjs.cloudflare.com",
               "https://cdn.jsdelivr.net"
             ],
             'style-src': ["'self'", "'unsafe-inline'"],
             'img-src': ["'self'", "data:"],
             'connect-src': ["'self'", "api.spotify.com"]
           }
           )


  from .routes import main


  app.register_blueprint(main)

  @app.after_request
  def set_security_headers(response):
    response.headers['CSP'] = (
      "default-src 'self'; "
      "script-src 'self'; "
      "style-src 'self'; "
      "img-src 'self' data:; "
      "font-src 'self'; "
      "frame-ancestors 'none';"
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

  @app.errorhandler(400)
  def bad_reqeust_400(error):
    current_app.logger.warning("Bad Request: %s %s", request.path, getattr(error, 'description', ''))
    return render_template('errors/400.html'), 400

  @app.errorhandler(403)
  def forbidden_403(error):
    current_app.logger.warning("Forbidden: %s from %s -- %s", request.path, request.remote_addr,
                               getattr(error, 'description', ''))
    return render_template('errors/403.html'), 403

  @app.errorhandler(404)
  def page_not_found_404(error):
    current_app.logger.info("Not Found: %s %s", request.path, request.remote_addr)
    return render_template('errors/404.html'), 404

  @app.errorhandler(500)
  def internal_server_error_500(error):
    current_app.logger.warning("Internal Server Error: %s", request.path)
    return render_template('errors/500.html'), 500

  @app.errorhandler(Exception)
  def handle_unexpected_error(error):
    current_app.logger.warning("Unexpected error: %s", error)
    return render_template('errors/500.html'), 500


  return app
