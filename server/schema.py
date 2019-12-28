import graphene
from graphql import GraphQLError
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from server.database.db import db
from server.database.models import Note, User



def require_auth(method):
    def wrapper(self, *args, **kwargs):
        auth_resp = User.decode_auth_token(args[0].context)
        if not isinstance(auth_resp, str):
            kwargs['user'] = User.query.filter_by(id=auth_resp).first()
            return method(self, *args, **kwargs)
        raise GraphQLError(auth_resp)

    return wrapper


class NoteObject(SQLAlchemyObjectType):
    class Meta:
        model = Note
        interfaces = (graphene.relay.Node,)


class UserObject(SQLAlchemyObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        exclude_fields = ('password_hash')


class Viewer(graphene.ObjectType):
    class Meta:
        interfaces = (graphene.relay.Node,)

    all_notes = SQLAlchemyConnectionField(NoteObject)
    all_users = SQLAlchemyConnectionField(UserObject)
    note = graphene.relay.Node.Field(NoteObject)
    user = graphene.relay.Node.Field(UserObject)


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    viewer = graphene.Field(Viewer)

    @staticmethod
    def resolve_viewer(root, info):
        auth_resp = User.decode_auth_token(info.context)
        if not isinstance(auth_resp, str):
            return Viewer()
        raise GraphQLError(auth_resp)


class SignUp(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(lambda: UserObject)
    auth_token = graphene.String()

    def mutate(self, info, **kwargs):
        user = User(username=kwargs.get('username'))
        user.set_password(kwargs.get('password'))
        db.session.add(user)
        db.session.commit()
        return SignUp(user=user, auth_token=user.encode_auth_token(user.id).decode())


class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(lambda: UserObject)
    auth_token = graphene.String()

    def mutate(self, info, **kwargs):
        user = User.query.filter_by(username=kwargs.get('username')).first()
        if user is None or not user.check_password(kwargs.get('password')):
            raise GraphQLError("Invalid Credentials")
        return Login(user=user, auth_token=user.encode_auth_token(user.id).decode())


class CreateNote(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        body = graphene.String(required=True)
        author_id = graphene.Int(required=True)

    note = graphene.Field(lambda: NoteObject)

    @require_auth
    def mutate(self, info, **kwargs):
        user = User.query.filter_by(id=kwargs.get('author_id')).first()
        note = Note(title=kwargs.get('title'), body=kwargs.get('body'))
        if user is not None:
            note.author = user
        db.session.add(note)
        db.session.commit()
        return CreateNote(note=note)


class UpdateNote(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        body = graphene.String(required=True)
        id = graphene.Int(required=True)

    note = graphene.Field(lambda: NoteObject)

    @require_auth
    def mutate(self, info, **kwargs):
        note = Note.query.filter_by(id=kwargs.get('id')).first()
        author = User.query.filter_by(id=note.author.id).first()
        if kwargs.get('user') != author:
            raise GraphQLError("You do not have permissions to update this post.")
        else:
            note.title = kwargs.get('title')
            note.body = kwargs.get('body')
            db.session.commit()
            return UpdateNote(note=note)


class DeleteNote(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    status = graphene.String()

    @require_auth
    def mutate(self, info, **kwargs):
        note = Note.query.filter_by(id=kwargs.get('id')).first()
        author = User.query.filter_by(id=note.author.id).first()
        if kwargs.get('user') != author:
            raise GraphQLError("You do not have permissions to delete this post.")
        else:
            db.session.delete(note)
            db.session.commit()
            return DeleteNote(status="OK")


class Mutation(graphene.ObjectType):
    create_note = CreateNote.Field()
    update_note = UpdateNote.Field()
    delete_note = DeleteNote.Field()
    signup = SignUp.Field()
    login = Login.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
