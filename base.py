import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy import ForeignKey

engine = sa.create_engine('sqlite:///database.db', echo=True)
SqlAlchemyBase = orm.declarative_base()


class Users(SqlAlchemyBase):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer,
                   primary_key=True,
                   autoincrement=True,
                   unique=True)
    login = sa.Column(sa.String(255),
                      nullable=False,
                      unique=True)
    password = sa.Column(sa.String(255),
                         nullable=False)
    recipes = orm.relationship("Recipes",
                               order_by="Recipes.id",
                               back_populates="user")
    comments = orm.relationship("Comments",
                                order_by="Comments.id",
                                back_populates="user")


class Recipes(SqlAlchemyBase):
    __tablename__ = 'recipes'
    id = sa.Column(sa.Integer,
                   primary_key=True,
                   autoincrement=True,
                   unique=True)
    user_id = sa.Column(sa.Integer,
                        ForeignKey('users.id'),
                        nullable=False)
    title = sa.Column(sa.String(255),
                      nullable=False)
    ingredients = sa.Column(sa.Text,
                            nullable=False)
    description = sa.Column(sa.Text,
                            nullable=False)
    image = sa.Column(sa.String(255),
                      nullable=True)
    user = orm.relationship("Users", back_populates="recipes")
    comments = orm.relationship("Comments",
                                order_by="Comments.id",
                                back_populates="recipe")


class Comments(SqlAlchemyBase):
    __tablename__ = 'comments'
    id = sa.Column(sa.Integer,
                   primary_key=True,
                   autoincrement=True,
                   unique=True)
    recipe_id = sa.Column(sa.Integer,
                          ForeignKey('recipes.id'),
                          nullable=False)
    user_id = sa.Column(sa.Integer,
                        ForeignKey('users.id'),
                        nullable=False)
    text = sa.Column(sa.Text,
                     nullable=False)
    recipe = orm.relationship("Recipes", back_populates="comments")
    user = orm.relationship("Users", back_populates="comments")


SqlAlchemyBase.metadata.create_all(bind=engine)
