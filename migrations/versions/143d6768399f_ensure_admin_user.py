"""ensure_admin_user

Revision ID: 143d6768399f
Revises: fadf1965f0e5
Create Date: 2023-09-11 13:37:40.521445

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from dundie.models.user import User
from sqlmodel import Session

# revision identifiers, used by Alembic.
revision = '143d6768399f'
down_revision = 'fadf1965f0e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    
    admin = User(
        name="Admin",
        username="admin",
        email="admin@dm.com",
        dept="management",
        currency="USD",
        password="admin", 
    )
    
    try:
        session.add(admin)
        session.commit()
    except sa.exc.IntegrityError:
        session.rollback()


def downgrade() -> None:
    pass
