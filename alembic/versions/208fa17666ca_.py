"""empty message

Revision ID: 208fa17666ca
Revises: 
Create Date: 2022-12-22 20:36:48.950213

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '208fa17666ca'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('professions',
    sa.Column('profession_id', sa.SMALLINT(), autoincrement=True, nullable=False),
    sa.Column('title', sa.VARCHAR(length=32), nullable=False),
    sa.PrimaryKeyConstraint('profession_id'),
    sa.UniqueConstraint('title')
    )
    op.create_table('university_directions',
    sa.Column('direction_id', sa.SMALLINT(), autoincrement=True, nullable=False),
    sa.Column('title', sa.VARCHAR(length=64), nullable=False),
    sa.PrimaryKeyConstraint('direction_id'),
    sa.UniqueConstraint('title')
    )
    op.create_table('forms',
    sa.Column('form_id', sa.SMALLINT(), autoincrement=True, nullable=False),
    sa.Column('full_name', sa.VARCHAR(length=64), nullable=False),
    sa.Column('birth_date', sa.DATE(), nullable=False),
    sa.Column('gender', sa.Enum('MALE', 'FEMALE', name='gendersenum'), nullable=False),
    sa.Column('phonenum', sa.VARCHAR(length=20), nullable=False),
    sa.Column('address', sa.VARCHAR(length=255), nullable=False),
    sa.Column('nation', sa.Enum('UZBEK', 'RUSSIAN', 'OTHER', name='nationsenum'), nullable=False),
    sa.Column('university_grade', sa.SMALLINT(), nullable=False),
    sa.Column('direction_id', sa.SMALLINT(), nullable=True),
    sa.Column('marital_status', sa.BOOLEAN(), nullable=False),
    sa.Column('driver_license', sa.BOOLEAN(), nullable=False),
    sa.Column('working_style', sa.Enum('COLLECTIVE', 'INDIVIDUAL', name='workingstylesenum'), nullable=False),
    sa.Column('wanted_salary', sa.SMALLINT(), nullable=False),
    sa.Column('positive_assessment', sa.TEXT(), nullable=False),
    sa.Column('negative_assessment', sa.TEXT(), nullable=False),
    sa.Column('photo_id', sa.TEXT(), nullable=False),
    sa.Column('registered_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['direction_id'], ['university_directions.direction_id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('form_id')
    )
    op.create_table('applications',
    sa.Column('application_id', sa.SMALLINT(), autoincrement=True, nullable=False),
    sa.Column('form_id', sa.SMALLINT(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=32), nullable=False),
    sa.Column('level', sa.SMALLINT(), nullable=False),
    sa.ForeignKeyConstraint(['form_id'], ['forms.form_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('application_id')
    )
    op.create_table('forms_professions',
    sa.Column('form_id', sa.SMALLINT(), nullable=False),
    sa.Column('profession_id', sa.SMALLINT(), nullable=False),
    sa.ForeignKeyConstraint(['form_id'], ['forms.form_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['profession_id'], ['professions.profession_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('form_id', 'profession_id')
    )
    op.create_table('languages',
    sa.Column('language_id', sa.SMALLINT(), autoincrement=True, nullable=False),
    sa.Column('form_id', sa.SMALLINT(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=32), nullable=False),
    sa.Column('level', sa.SMALLINT(), nullable=False),
    sa.ForeignKeyConstraint(['form_id'], ['forms.form_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('language_id')
    )
    op.create_table('users',
    sa.Column('telegram_id', sa.BIGINT(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=255), nullable=True),
    sa.Column('telegram_name', sa.VARCHAR(length=255), nullable=False),
    sa.Column('form_id', sa.SMALLINT(), nullable=True),
    sa.Column('registered_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['form_id'], ['forms.form_id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('telegram_id'),
    sa.UniqueConstraint('form_id')
    )
    op.create_table('working_companies',
    sa.Column('form_id', sa.SMALLINT(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=255), nullable=False),
    sa.Column('position', sa.VARCHAR(length=255), nullable=False),
    sa.ForeignKeyConstraint(['form_id'], ['forms.form_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('form_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('working_companies')
    op.drop_table('users')
    op.drop_table('languages')
    op.drop_table('forms_professions')
    op.drop_table('applications')
    op.drop_table('forms')
    op.drop_table('university_directions')
    op.drop_table('professions')
    # ### end Alembic commands ###
