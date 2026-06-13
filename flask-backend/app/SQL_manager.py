import csv
import os

import dotenv
import pymysql
import pymysql.cursors
from flask import g

dotenv.load_dotenv()

host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
database = os.getenv("DB_NAME")
port = int(os.getenv("DB_PORT"))


def get_db():
  return pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    port=port,
    local_infile=True,
    cursorclass=pymysql.cursors.DictCursor)
  #if current request doesn't have a DB connection yet make one
  if 'db' not in g:
    g.db = pymysql.connect(
      host=host,
      user=user,
      password=password,
      database=database,
      port=port,
      cursorclass=pymysql.cursors.DictCursor
    )
  return g.db

def run_query(connection, sql, args=None):

  with connection.cursor() as cursor:
    cursor.execute(sql, args)
    if sql.strip().upper().startswith("SELECT"):
      return cursor.fetchall()

    connection.commit()
    return cursor.rowcount

import uuid

import uuid
import json
from datetime import datetime


def get_all_users_sql():
  query = "SELECT * FROM User"
  try:
    connection = get_db()
    params = []
    return run_query(connection, query, params)

  except Exception as e:
    print(f"Query Failed: {e}")
    return False

def select_users_sql(user_ids):
  format_strings = ','.join(['%s'] * len(user_ids))
  query = f"SELECT * FROM users WHERE id IN ({format_strings})"
  try:
    connection = get_db()
    params = [id]
    return run_query(connection, query, params)

  except Exception as e:
    print(f"Query Failed: {e}")
    return False

def get_user_data_from_name_sql(name):
  query = "SELECT * FROM User WHERE username = %s LIMIT 1"
  try:
    connection = get_db()
    params = [name]
    return run_query(connection, query, params)

  except Exception as e:
    print(f"Query Failed: {e}")
    return False

def is_name_taken(name):
  query = "SELECT * FROM User WHERE username = %s LIMIT 1"
  try:
    connection = get_db()
    params = [name]
    results = run_query(connection, query, params)

    return bool(results)

  except Exception as e:
    print(f"Query Failed: {e}")
    return False

  except Exception as e:
    print(f"Query Failed: {e}")
    return False

def create_user_sql(name,passkey,role = "player"):
  query = "INSERT INTO User (username,hashedpassword,role) VALUES (%s,%s,%s)"

  try:
    connection = get_db()
    params = [name,passkey,role]
    run_query(connection, query, params)
    return True

  except Exception as e:
    print(f"Query Failed: {e}")
    return False

def get_image_batch_sql(batch_size,user_id):
  try:

    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("START TRANSACTION")

    # Lock and select
    cursor.execute("""
                   SELECT image_id FROM Image
                   WHERE status = 'Waiting'
                     LIMIT %s FOR UPDATE SKIP LOCKED
                   """, (batch_size,))

    locked_images = cursor.fetchall()
    if not locked_images:
      cursor.execute("COMMIT")
      return [] # No images waiting

    # Extract just the IDs into a flat list
    image_ids = [row["image_id"] for row in locked_images]
    # Update the Image table
    format_strings = ','.join(['%s'] * len(image_ids))
    update_query = f"UPDATE Image SET status = 'Processing' WHERE image_id IN ({format_strings})"
    cursor.execute(update_query, tuple(image_ids))

    #  Insert the new Jobs
    job_data = [(user_id, img_id) for img_id in image_ids]
    cursor.executemany("INSERT INTO Job (user_id, image_id) VALUES (%s, %s)", job_data)

    cursor.execute("COMMIT")

    return image_ids

  except Exception as e:

    cursor.execute("ROLLBACK")
    print(e)
    return False



def get_user_contributions_sql(user_id):
  query = "SELECT COUNT(*) FROM Job WHERE user_id = %s AND status = 'Completed'"
  try:
    connection = get_db()
    params = [user_id]
    return run_query(connection, query, params)

  except Exception as e:
    print(f"Query Failed: {e}")
    return False


def get_total_contributions_sql():
  query = """
          SELECT AVG(status = 'Completed') * 100 AS percent_completed
          FROM Image;
  """
  try:
    connection = get_db()
    params = []
    return run_query(connection, query, params)


  except Exception as e:
    print(f"Query Failed: {e}")
    return False

import csv

import os

import csv

def save_images_to_database(spots_csv_dir):
  # Base query without the VALUES clause
  base_query = """
               INSERT INTO Image (image_id, OSM_tags, freestyle_rating, cinematic_rating, obstacle_density, busyness)
               VALUES \
               """

  try:
    connection = get_db()
    cursor = connection.cursor()

    with open(spots_csv_dir, mode='r', newline='', encoding='utf-8') as file:
      reader = csv.DictReader(file)

      chunk = []
      for row in reader:
        # Build the row tuple: (id, data, 0, 0, 0, 0)
        chunk.append((row['id'], row['data'], 0, 0, 0, 0))

        # Once we hit 5,000 rows, execute them in one single SQL statement
        if len(chunk) >= 5000:
          # Creates: VALUES (%s,%s,0,0,0,0), (%s,%s,0,0,0,0), ...
          value_placeholders = ", ".join(["(%s, %s, %s, %s, %s, %s)"] * len(chunk))
          # Flatten the chunk list of tuples into a single flat list for the execution
          flat_params = [item for row_tuple in chunk for item in row_tuple]

          cursor.execute(base_query + value_placeholders, flat_params)
          connection.commit()
          chunk = [] # Clear the chunk

      # Catch any leftover rows at the end of the file
      if chunk:
        value_placeholders = ", ".join(["(%s, %s, %s, %s, %s, %s)"] * len(chunk))
        flat_params = [item for row_tuple in chunk for item in row_tuple]
        cursor.execute(base_query + value_placeholders, flat_params)
        connection.commit()

    cursor.close()
    return True

  except Exception as e:
    print(f"Query Failed: {e}")
    if connection: connection.rollback()
    return False
#save_images_to_database("/Users/tamair/IdeaProjects/Distributed-Machines/flask-backend/app/static/master_candidates_reduced.csv")