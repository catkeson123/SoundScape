#!/usr/bin/env python3

# Standard library imports

# Remote library imports
from flask import Flask, request, make_response, jsonify, session
from flask_migrate import Migrate
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError

# Local imports
from config import app, db, api, bcrypt
from models import db, User, Album, Review

# Views
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False
app.secret_key = 'b​​\xe6!\xf6p\xd75\x81\x97\x8f\xe7%\x92\xb5.\x04\xee'

migrate = Migrate(app, db)

db.init_app(app)
api = Api(app)

class Home(Resource):
    def get(self):
        return "Welcome to SoundScape"
    
api.add_resource(Home, '/')

@app.before_request
def check_if_logged_in():
    if ("user_id" not in session or not session['user_id']) \
        and request.endpoint == 'users' :
        return {'error': 'Unauthorized'}, 401

class Users(Resource):
    def get(self):
        u_list = [u.user_dict() for u in User.query.all()]
        # users =User.query.all()
        # u_list=[]
        # for user in users:
        #     u=user.user_dict()
        #     u_list.append(u)
        return make_response(u_list, 200)
    def post(self):
        data = request.get_json()
        try:
            new_user = User(first_name=data['first_name'], last_name=data['last_name'], user_name=data['user_name'], email=data['email'], picture=data['picture'], password_hash=data['password'])
            db.session.add(new_user)
            db.session.commit()
        except:
            return make_response({'error': 'All inputs need valid data'}, 422)
        
        return make_response(new_user.user_dict(), 201)
    
api.add_resource(Users, '/users', endpoint='users')

class UserByID(Resource):
    def get(self, id):
        u = User.query.filter_by(id=id).first()
        if u == None:
            return make_response({'error': 'User not found'}, 404) 
        return make_response(u.user_dict(), 200)
    
    def patch(self, id):
        data = request.get_json()
        user = User.query.filter_by(id=id).first()
        if user == None:
            return make_response({'error': 'User not found'}, 404)

        for attr in data:
            setattr(user, attr, data[attr])

        try:
            db.session.add(user)
            db.session.commit()
        except:
            db.session.rollback()
            return make_response({'error': 'validation errors'}, 422)

        response_dict = user.user_dict()

        response = make_response(response_dict, 200)

        return response
    def delete(self, id):
        user = User.query.filter_by(id=id).first()
        if user == None:
            return make_response({'error': 'User not found'}, 404)

        db.session.delete(user)
        db.session.commit()

        return make_response('User Deleted', 201)

api.add_resource(UserByID, '/users/<int:id>')

class Albums(Resource):
    def get(self):
        a_list = [a.to_dict() for a in Album.query.all()]
        return make_response(a_list, 200)
    
api.add_resource(Albums, '/albums')

class Reviews(Resource):
    def get(self):
        r_list = [r.review_dict() for r in Review.query.all()]
        return make_response(r_list, 200)
    def post(self):
        data = request.get_json()
        if data['user_id'] == None or data['album_id'] == None or data['rating'] == None:
            db.session.rollback()
            return make_response({'error': 'All inputs need valid data'}, 422)
        else:
            new_rev = Review(
                user_id=data['user_id'], album_id=data['album_id'], rating=data['rating'], comment=data['comment'])

            try:
                db.session.add(new_rev)
                db.session.commit()
            except:
                db.session.rollback()
                return make_response({'error': 'All inputs need valid data'}, 422)

            rev_dict = new_rev.review_dict()
            return make_response(rev_dict, 201)

api.add_resource(Reviews, '/reviews', endpoint='reviews')

class ReviewByID(Resource):
    def patch(self, id):
        data = request.get_json()
        rev = Review.query.filter_by(id=id).first()
        if rev == None:
            return make_response({'error': 'Review not found'}, 404)

        for attr in data:
            setattr(rev, attr, data[attr])

        try:
            db.session.add(rev)
            db.session.commit()
        except:
            db.session.rollback()
            return make_response({'error': 'validation errors'}, 422)

        response_dict = rev.review_dict()

        response = make_response(response_dict, 200)

        return response
    def delete(self, id):
        rev = Review.query.filter_by(id=id).first()
        if rev == None:
            return make_response({'error': 'Review not found'}, 404)

        db.session.delete(rev)
        db.session.commit()

        return make_response({'msg': 'Review Deleted'}, 201)

api.add_resource(ReviewByID, '/reviews/<int:id>')

class Login(Resource):

    def get(self):
        ...

    def post(self):
        username = request.get_json()['username']
        user = User.query.filter(User.user_name == username).first()

        password = request.get_json()['password']

        if user.authenticate(password):
            session['user_id'] = user.id
            return user.user_dict(), 200

        return {'error': 'Invalid username or password'}, 401

api.add_resource(Login, '/login')

class SignUp(Resource):
    
    def post(self):
        data = request.get_json()
        try:
            if data['picture'] == None or data['picture'] == '':
                new_user = User(first_name=data['firstName'], last_name=data['lastName'], user_name=data['username'], email=data['email'], picture="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR82DN9JU-hbIhhkPR-AX8KiYzA4fBMVwjLAG82fz7GLg&s", password_hash=data['password'])
            else:
                new_user = User(first_name=data['firstName'], last_name=data['lastName'], user_name=data['username'], email=data['email'], picture=data['picture'], password_hash=data['password'])
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
        except:
            return make_response({'error': 'All inputs need valid data'}, 422)
        
        return make_response(new_user.user_dict(), 201)
    
api.add_resource(SignUp, '/signup')

class CheckSession(Resource):

    def get(self):
        user = User.query.filter(User.id == session.get('user_id')).first()
        if user:
            return user.user_dict()
        else:
            return {'message': '401: Not Authorized'}, 401

api.add_resource(CheckSession, '/check_session')

class Logout(Resource):

    def delete(self):
        session['user_id'] = None
        return {'message': '204: No Content'}, 204

api.add_resource(Logout, '/logout')

class FollowById(Resource):
    def post(self, id):

        user_to_follow = User.query.filter_by(id = id).first()
        current_user = User.query.filter(User.id == session.get('user_id')).first()

        if not current_user.is_following(user_to_follow):
            current_user.followed.append(user_to_follow)
            db.session.commit()
            return make_response(user_to_follow.user_dict(), 201)
        else:
            return make_response({'message': 'You are already following this user.'}, 201)

api.add_resource(FollowById, '/follow/<int:id>')

class UnfollowById(Resource):
    def delete(self, id):

        current_user = User.query.filter(User.id == session.get('user_id')).first()
        followed_user = User.query.filter_by(id = id).first()

        current_user.unfollow(followed_user)
        db.session.commit()

        return make_response({'message': 'User Unfollowed'}, 200)
    
api.add_resource(UnfollowById, '/unfollow/<int:id>')

class CheckFollowById(Resource):
    def get(self, id):
        current_user = User.query.filter(User.id == session.get('user_id')).first()
        checking_user = User.query.filter_by(id = id).first()

        if current_user.is_following(checking_user):
            return make_response(jsonify({'following': True}), 200)
        else:
            return make_response(jsonify({'following': False}), 200)

api.add_resource(CheckFollowById, '/check/<int:id>')

class LikeById(Resource):
    def post(self, id):

        review = Review.query.filter_by(id = id).first()
        current_user = User.query.filter(User.id == session.get('user_id')).first()

        if not current_user.has_liked_review(review):
            current_user.like_review(review)
            db.session.commit()
            return make_response(review.review_dict(), 201)
        else:
            return make_response({'message': 'You have already liked this review.'}, 201)
        
api.add_resource(LikeById, '/like/<int:id>')

class UnlikeById(Resource):
    def delete(self, id):

        current_user = User.query.filter(User.id == session.get('user_id')).first()
        review = Review.query.filter_by(id = id).first()

        current_user.unlike_review(review)
        db.session.commit()

        return make_response({'message': 'Review Unliked'}, 200)
    
api.add_resource(UnlikeById, '/unlike/<int:id>')

class CheckLikeById(Resource):
    def get(self, id):
        current_user = User.query.filter(User.id == session.get('user_id')).first()
        review = Review.query.filter_by(id = id).first()

        if current_user.has_liked_review(review):
            return make_response(jsonify({'liked': True}), 200)
        else:
            return make_response(jsonify({'liked': False}), 200)

api.add_resource(CheckLikeById, '/checklike/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
