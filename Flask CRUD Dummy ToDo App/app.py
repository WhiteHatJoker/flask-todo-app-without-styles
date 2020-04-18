from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:postgres@localhost:5432/todo'
db = SQLAlchemy(app)


migrate = Migrate(app, db)


class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id', ondelete='cascade'), nullable=False)

    def __repr__(self):
        return f'<Todo {self.id} {self.description}>'


class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    todos = db.relationship('Todo', backref='list', lazy=True, cascade='all, delete-orphan')


# We don't need to use db.create_all() since flask db init and  flask db migrate creates tables automatically


@app.route('/')
def index():
    return redirect(url_for('get_list_todos', list_id=1))


@app.route('/lists/<list_id>')
def get_list_todos(list_id):
    return render_template('index.html', lists=TodoList.query.order_by('id').all(), active_list=TodoList.query.get(list_id), todos=Todo.query.filter_by(list_id=list_id).order_by('id').all())


@app.route('/todos/create', methods=['POST'])
def create_todo():
    error = False
    body = {}
    try:
        list_id = request.get_json()['active_list']
        description = request.get_json()['description']
        todo = Todo(description=description, list_id=list_id)
        db.session.add(todo)
        db.session.commit()
        body['description'] = todo.description
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        return jsonify(body)


@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
def set_completed_todo(todo_id):
    try:
        completed = request.get_json()['completed']
        todo = Todo.query.get(todo_id)
        todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})


@app.route('/todos/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    success = True
    try:
        Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
        success = False
    finally:
        db.session.close()
    return jsonify({'success': success})


@app.route('/lists/create', methods=['POST'])
def create_todolist():
    try:
        name = request.form.get('list_name', 'Unnamed')
        todolist = TodoList(name=name)
        db.session.add(todolist)
        db.session.commit()
        id = todolist.id
    except:
        db.session.rollback()
    finally:
        db.session.close()
        return redirect(url_for('get_list_todos', list_id=id))


@app.route('/lists/<list_id>/set-completed', methods=['POST'])
def set_completed_list(list_id):
    try:
        completed = request.get_json()['completed']
        list = TodoList.query.get(list_id)
        list.completed = completed
        todos = Todo.query.filter_by(list_id=list_id).all()
        for todo in todos:
            todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})


@app.route('/lists/<list_id>', methods=['DELETE'])
def delete_list(list_id):
    success = True
    try:
        TodoList.query.filter_by(id=list_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
        success = False
    finally:
        db.session.close()
    return jsonify({'success': success})


if __name__ == '__main__':
    app.run(debug=True)
