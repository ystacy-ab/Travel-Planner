# Travel-Planner

## Technology Choices

- Framework: Flask  
Flask was chosen because it is a lightweight and flexible micro-framework. I have prior experience working with it, which allowed for rapid, efficient development of the API structure without unnecessary overhead.
- Database: MySQL  
MySQL was selected because it perfectly handles requirements and I am already familiar with configuring and querying it.

## How It Works

1. Users create a travel project.
2. Users add up to 10 places to a project using an external_id from the third-party API. The backend automatically validates this ID.
3. Users can attach notes to these places and update them over time.
4. Users can mark a place as visited.
5. When all places within a project are marked as visited, the project's status automatically updates to completed.
6. A project cannot be deleted if any of its places are marked as visited.

## Database Structure

The database consists of two tables with a one-to-many relationship.

- **projects**: Stores the core project information including name, description, start date, and current status.
- **project_places**: Stores the places associated with a project. It uses project_id as a foreign key and holds the external_id, fetched details, user notes, and the visited (bool).

![Database Schema](db.png)

## API Endpoints

### Projects

- `POST /projects` - Create a new travel project (can include an initial array of places).
- `GET /projects` - Retrieve a summary list of all projects.
- `GET /projects/<project_id>` - Retrieve details of a specific project, including its places.
- `PUT /projects/<project_id>` - Update a project's name, description, or start date.
- `DELETE /projects/<project_id>` - Delete a project (fails if any place is visited).

### Places

- `POST /projects/<project_id>/places` - Add a new place to an existing project.
- `GET /projects/<project_id>/places` - List all places for a specific project.
- `GET /projects/<project_id>/places/<place_id>` - Get details for a specific place.
- `PUT /projects/<project_id>/places/<place_id>` - Update a place's notes or mark it as visited.


## How to Run

- Clone the repository and navigate to the project directory
- Install the required dependencies:

```
pip install -r requirements.txt
```
- Create a local MySQL database named travel_db and configure the environment variable:

```
export DATABASE_URL="mysql+pymysql://your_username:your_password@localhost/travel_db"

# On Windows: 
set DATABASE_URL="mysql+pymysql://your_username:your_password@localhost/travel_db"
```
- Start the Flask server:

```
python3 app.py
```
*The application will automatically generate the database tables upon the first startup and run on http://127.0.0.1:5001.*

## Testing

The entire application, including endpoint routing, error handling, third-party API validation, and database constraints, was manually tested using Postman.

## Postman Collection

You can find the specification in the `Travel App API.postman_collection.json` file included in this repository.

### How to use with Postman:
1. Open Postman
2. Import file from the repository
3. Start the server and test the endpoints
