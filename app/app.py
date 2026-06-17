"""main"""
import os
from datetime import datetime
import requests
from flask import Flask, request, jsonify
from models import db, Project, ProjectPlace

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:password@localhost/travel_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

ART_API_URL = "https://api.artic.edu/api/v1/artworks"

def validate_place(external_id):
    """
    Args:
        external_id (str or int): unique artwork identifier

    Returns:
        dict: contains validation status ('is_valid') and artwork details
              ('title') if found, or just {'is_valid': False} if not.
    """
    try:
        response = requests.get(f"{ART_API_URL}/{external_id}")
        if response.status_code == 200:
            data = response.json().get('data', {})
            return {
                "is_valid": True,
                "title": data.get('title')
            }
        return {"is_valid": False}
    except Exception:
        return {"is_valid": False}

with app.app_context():
    db.create_all()

@app.route('/projects', methods=['POST'])
def create_project():
    """
    Create a new travel project
    Returns:
        tuple: JSON response
    """
    data = request.json
    if not data or not data.get('name'):
        return jsonify({"error": "Name is required"}), 400
    new_project = Project(
        name=data['name'],
        description=data.get('description'),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None
    )
    db.session.add(new_project)
    db.session.flush()
    places_data = data.get('places', [])
    if len(places_data) > 10:
        db.session.rollback()
        return jsonify({"error": "Maximum 10 places allowed per project"}), 400
    added_external_ids = set()
    for place_data in places_data:
        ext_id = str(place_data.get('external_id'))
        if not ext_id or ext_id in added_external_ids:
            continue
        validation = validate_place(ext_id)
        if not validation["is_valid"]:
            db.session.rollback()
            return jsonify({"error": f"Place with external_id {ext_id} not found in Art Institute API"}), 400
        new_place = ProjectPlace(
            project_id=new_project.id,
            external_id=ext_id,
            title=validation["title"],
            notes=place_data.get('notes')
        )
        db.session.add(new_place)
        added_external_ids.add(ext_id)
    db.session.commit()
    return jsonify({"id": new_project.id, "message": "Project created"}), 201

@app.route('/projects', methods=['GET'])
def list_projects():
    """
    Returns:
        tuple: JSON response (an array of project dictionaries + HTTP status code)
    """
    projects = Project.query.all()
    result = []
    for p in projects:
        result.append({
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "start_date": p.start_date.isoformat() if p.start_date else None
        })
    return jsonify(result), 200

@app.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """
    Args:
        project_id (int): unique project identifier

    Returns:
        tuple: JSON response (project details and its associated places + HTTP status code)
    """
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "status": project.status,
        "places": [{"id": pl.id, "external_id": pl.external_id, "title": pl.title, "visited": pl.visited} for pl in project.places]
    }), 200

@app.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """
    Args:
        project_id (int): unique project identifier
    Returns:
        tuple: JSON response
    """
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    data = request.json
    if 'name' in data:
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']
    if 'start_date' in data:
        project.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data['start_date'] else None
    db.session.commit()
    return jsonify({"message": "Project updated"}), 200

def update_project_status(project_id):
    """
    Checks if all places in a project are visited and updates the project status accordingly.

    Args:
        project_id (int): unique project identifier

    Returns:
        None
    """
    project = db.session.get(Project, project_id)
    if not project or not project.places:
        return
    all_visited = all(place.visited for place in project.places)
    if all_visited and project.status != 'completed':
        project.status = 'completed'
        db.session.commit()
    elif not all_visited and project.status != 'planning':
        project.status = 'planning'
        db.session.commit()

@app.route('/projects/<int:project_id>/places', methods=['POST'])
def add_place(project_id):
    """
    Args:
        project_id (int): unique project identifier
    Returns:
        tuple: JSON response (ID of the new place and a success message + HTTP status code)
    """
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if len(project.places) >= 10:
        return jsonify({"error": "Project already has maximum of 10 places"}), 400

    data = request.json
    ext_id = str(data.get('external_id'))
    if any(p.external_id == ext_id for p in project.places):
        return jsonify({"error": "Place already exists in this project"}), 400
    validation = validate_place(ext_id)
    if not validation["is_valid"]:
        return jsonify({"error": "Place not found in Art Institute API"}), 400
    new_place = ProjectPlace(
        project_id=project.id,
        external_id=ext_id,
        title=validation["title"],
        notes=data.get('notes')
    )
    db.session.add(new_place)
    db.session.commit()
    update_project_status(project.id)
    return jsonify({"id": new_place.id, "message": "Place added"}), 201

@app.route('/projects/<int:project_id>/places', methods=['GET'])
def list_places(project_id):
    """
    Args:
        project_id (int): unique project identifier
    Returns:
        tuple: JSON response (array of place dictionaries + HTTP status code)
    """
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    places = [{"id": p.id, "title": p.title, "visited": p.visited, "notes": p.notes} for p in project.places]
    return jsonify(places), 200

@app.route('/projects/<int:project_id>/places/<int:place_id>', methods=['GET'])
def get_place(project_id, place_id):
    """
    Args:
        project_id (int): unique project identifier
        place_id (int): unique place identifier

    Returns:
        tuple: JSON response (place details + HTTP status code) 
    """
    place = ProjectPlace.query.filter_by(id=place_id, project_id=project_id).first()
    if not place:
        return jsonify({"error": "Place not found"}), 404
    return jsonify({
        "id": place.id,
        "external_id": place.external_id,
        "title": place.title,
        "notes": place.notes,
        "visited": place.visited
    }), 200

@app.route('/projects/<int:project_id>/places/<int:place_id>', methods=['PUT'])
def update_place(project_id, place_id):
    """
    Updates specific attributes (notes, visited status) of a place within a project.

    Args:
        project_id (int): unique project identifier
        place_id (int): unique place identifier

    Returns:
        tuple: JSON response containing a success message + HTTP status code.
    """
    place = ProjectPlace.query.filter_by(id=place_id, project_id=project_id).first()
    if not place:
        return jsonify({"error": "Place not found"}), 404
    data = request.json
    if 'notes' in data:
        place.notes = data['notes']
    if 'visited' in data:
        place.visited = bool(data['visited'])
    db.session.commit()
    update_project_status(project_id)
    return jsonify({"message": "Place updated"}), 200

@app.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Args:
        project_id (int): unique project identifier

    Returns:
        tuple: JSON response
    """
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    for place in project.places:
        if place.visited:
            return jsonify({"error": "Cannot delete project with visited places"}), 400
    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
