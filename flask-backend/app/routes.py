import flask
import jwt
from PIL import Image
from flask import Blueprint, render_template, jsonify, request, Config
import os
import tempfile
import subprocess
from datetime import datetime, timedelta, timezone
import uuid
from werkzeug.utils import secure_filename
import PIL
from pillow_heif import register_heif_opener
import bcrypt
from flask import request, jsonify, make_response
UPLOAD_FOLDER = '/app/static/uploads'
SECRET_KEY = "5565a1fa45aec75ad7be7462bd31b0be1f9601a73074910f4dc214d563c3e94f"
main = Blueprint('main', __name__)
from .SQL_manager import *
from functools import wraps
def token_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    token = request.cookies.get('access_token')

    if not token:
      return jsonify({"error": "Unauthorized"}), 401

    try:
      # Verify the token
      decoded_data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
      # Pass the user_id into the route as an argument
      current_user_id = decoded_data['id']
    except jwt.ExpiredSignatureError:
      return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
      return jsonify({"error": "Invalid token"}), 401

    return f(current_user_id, *args, **kwargs)

  return decorated


@main.route('/api/BOB')
def index():
  data = "BOB"
  return jsonify(data)

@main.route('/api/get-users')
def get_users():
  all_users = get_all_users_sql()
  print(all_users)
  return jsonify(all_users)

from flask import send_from_directory

@main.route('/static/uploads/<filename>')
def serve_uploaded_media(filename):
  # This tells Flask exactly where to fetch the files we just saved
  return send_from_directory('/app/static/uploads', filename)


@main.route('/api/login-user',methods=['POST'])
def login_user():
  user_data = request.get_json()
  if not user_data:
    return jsonify({"status": "failed", "received": user_data})
  print(user_data)
  user = get_user_data_from_name_sql(user_data['name'])

  if not user or not bcrypt.checkpw(user_data['passkey'].encode('utf-8'), user[0]['hashedpassword'].encode('utf-8')):
    return jsonify({"status": "failed", "received": "Wrong credentials"}), 401

  token = jwt.encode({
    'id': user[0]['id'],
    'exp': datetime.utcnow() + timedelta(hours=1)
  }, SECRET_KEY, algorithm="HS256")

  safe_profile = {
    "id": user[0]['id'],
    "name": user[0]['username'],
  }
  resp = make_response(jsonify({"status": "success", "received": safe_profile}))

  resp.set_cookie(
    'access_token',
    token,
    httponly=True,
    samesite='Lax',
    secure=False    # Set to True in production so it only sends over HTTPS
  )

  return resp



@main.route('/api/create-user',methods=['POST'])
def create_user():
  user_data = request.get_json()
  print(user_data)
  if not user_data:
    return jsonify({"status": "failed", "received": user_data})

  out = is_name_taken(user_data['name'])
  if not out:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user_data['passkey'].encode('utf-8'), salt)
    create_user_sql(user_data['name'],hashed_password)
  else:
    return jsonify({"status": "failed", "received": "Taken"})

  return jsonify({"status": "success", "received": user_data})


@main.route('/api/get-contributions',methods=['POST'])
@token_required
def get_contributions(current_user_id):

  total =  get_total_contributions_sql()
  user_con = get_user_contributions_sql(current_user_id)

  data = {"total_progress" : total,
          "user_con" : user_con}

  return jsonify(data)

@main.route('/api/get-batch-photos',methods=['POST'])
@token_required
def get_batch_photos(current_user_id):
  request_data = request.get_json()
  amount = request_data.get('amount', 10)

  images = get_image_batch_sql(amount,current_user_id)

  if not images:
    return jsonify({"status": "Failed", "received": images})

  return jsonify({"status": "Success", "received": images})

PROMPT = """
You are a critical, highly selective FPV drone pilot vetting satellite imagery for elite freestyle and cinematic flight locations. 
Most locations are boring and should receive very low scores. Reserve high scores (0.8+) ONLY for exceptional, highly clear structural features or scenic landmarks.

Analyze the provided top-down satellite image alongside its OpenStreetMap data. 
CRITICAL DEPTH CUES: Top-down imagery hides elevation. You MUST actively look for high-contrast shadow lines, deep carved riverbeds, gorges, and jagged rock textures. These indicate steep, diveable cliffs.
CRITICAL HUMAN CUES: Tiny colored dots on beaches or in parks are people. Rectangles near buildings or roads are cars. 

### SCORING CALIBRATION RUBRIC (Apply strictly):

1. `freestyle_rating` (0.0 to 1.0):
   - 0.0 to 0.3: Open grass fields, standard parks, flat terrain, basic green fields.
   - 0.4 to 0.7: Moderate tree canopies, active industrial parks with flat rooftops, standard multi-story buildings.
   - 0.7 to 1.0: Abandoned structures (bandos), multi-level concrete ruins, tight architectural gaps, deep carved riverbeds/gorges, or isolated bridges crossing natural gaps (look for linear structures spanning dark shadowed areas).

2. `cinematic_rating` (0.0 to 1.0):
   - 0.0 to 0.2: Generic suburban roofs, flat fields, standard motorways. 
   - 0.3 to 0.6: Rolling hills (smooth textures), uniform forests, standard rivers.
   - 0.7 to 1.0: Striking geographic features, jagged mountain ridges/cliffs (heavy rock textures and long shadows), lone historical structures, epic valley views.

3. `obstacle_density` (0.0 to 1.0):
   - 0.0: Perfectly flat, empty grass/sand.
   - 0.5: Scattered trees, light suburban housing, single-lane roads.
   - 1.0: Dense structural steel, crane yards, thick forest canopy, complex ruins, dense jagged rock formations in gorges.

4. `busyness` (0.0 to 1.0):
   - 0.0: Total abandonment, remote wilderness, zero signs of human life.
   - 0.3: Very remote, maybe a lone dirt road, absolutely zero cars or people.
   - 0.6: Sparse houses, quiet rural roads, empty parks.
   - 0.8 to 1.0: ANY visible people (dots on a beach/park), parked or moving cars, dense residential neighborhoods, or active commercial buildings. If humans or their cars are there, score it high.

### OUTPUT FORMAT:
Return ONLY a raw, valid JSON object. No markdown code blocks. No pre-text or post-text.

{
  "freestyle_rating": float,
  "cinematic_rating": float,
  "obstacle_density": float,
  "busyness": float
}

### OPENSTREETMAP CONTEXT DATA:
The OpenStreetMap tags associated with this exact coordinate location are:
"""

@main.route('/api/get-prompt',methods=['POST'])
@token_required
def get_prompt(current_user_id):
  return jsonify({"status": "Success", "received": PROMPT})



