# Load logging configuration
import logging
import sys
from server.database.models import User
from server.database.db import db

log = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


if __name__ == '__main__':
    log.info('Create database')
    user = User(username='admin')
    user.set_password('admin')
    from server.app import app
    with app.app_context():
        db.create_all()
        db.session.add(user)
        db.session.commit()
