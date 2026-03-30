from models import db, Paper, Thread, Message


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()


def create_paper(filename, content):
    paper = Paper(filename=filename, content=content)
    db.session.add(paper)
    db.session.commit()
    return paper.id


def get_all_papers():
    return Paper.query.all()


def get_paper(paper_id):
    return Paper.query.get(paper_id)


def delete_paper(paper_id):
    paper = Paper.query.get(paper_id)
    db.session.delete(paper)
    db.session.commit()


def update_paper(paper_id, new_filename):
    paper = Paper.query.get(paper_id)
    paper.filename = new_filename
    db.session.commit()


def create_thread(name=None, user_id=None):
    thread = Thread(name=name, user_id=user_id)
    db.session.add(thread)
    db.session.commit()
    return thread.id


def get_threads():
    return Thread.query.order_by(
        Thread.created_at.desc()
    ).all()


def add_message(thread_id, role, content):
    msg = Message(
        thread_id=thread_id,
        role=role,
        content=content,
    )
    db.session.add(msg)
    db.session.commit()


def get_messages(thread_id):
    return (
        Message.query.filter_by(thread_id=thread_id)
        .order_by(Message.created_at.asc())
        .all()
    )