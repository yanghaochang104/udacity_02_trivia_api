import os
from flask import Flask, json, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import sys
import sqlalchemy

from sqlalchemy.orm.query import Query
from werkzeug.exceptions import NotFound

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# no next question and stop quiz


class NoMoreQuestions(Exception):
    pass


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authoriaztion, true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, PUT, POST, DELETE, OPTIONS')
        return response

    @app.route('/categories', methods=['GET'])
    # get all categories
    def get_categories():
        try:
            categories = Category.query.all()
            formatted_categories = {
                category.id: category.type for category in categories
            }
            return jsonify({
                'success': True,
                'categories': formatted_categories,
            })
        except Exception:
            abort(422)

    @app.route('/questions', methods=['GET'])
    # get questions in list page without select specific category
    def get_questions():
        try:
            # pagination
            page = request.args.get('page', 1, type=int)
            start = (page-1) * 10
            end = page * 10

            questions = Question.query.all()
            formatted_questions = [question.format() for question in questions]
            current_formatted_questions = formatted_questions[start:end]

            if len(current_formatted_questions) == 0:
                raise NotFound

            categories = Category.query.all()
            formatted_categories = {
                category.id: category.type for category in categories
            }
            return jsonify({
                'success': True,
                'questions': current_formatted_questions,
                'total_questions': len(formatted_questions),
                'categories': formatted_categories,
                'current_category': 0
            })
        except NotFound:
            abort(404)
        except Exception:
            abort(422)

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    # delete question
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                raise NotFound

            question.delete()
            return jsonify({
                'success': True,
                'message': 'Question Deleted'
            })
        except NotFound:
            abort(404)
        except Exception:
            abort(422)

    @app.route('/add/questions', methods=['POST'])
    # adding a question into a category
    def create_question():
        try:
            body = request.get_json()
            question = body.get('question', None)
            answer = body.get('answer', None)
            category = body.get('category', None)
            difficulty = body.get('difficulty', None)
            new_question = Question(
                question=question, answer=answer, category=category, difficulty=difficulty)
            new_question.insert()
            return jsonify({
                'success': True,
                'message': 'Question Added'
            }), 201
        except Exception:
            abort(422)

    @app.route('/questions', methods=['POST'])
    # search question with key word
    def search_question():
        try:
            body = request.get_json()
            formatted_target_question = []
            searchTerm = body.get('searchTerm', None)
            if searchTerm is not '':
                target_questions = Question.query.filter(
                    Question.question.ilike('%{}%'.format(searchTerm))).all()
                formatted_target_question = [
                    target_question.format() for target_question in target_questions]
            return jsonify({
                'questions': formatted_target_question,
                'total_questions': len(formatted_target_question),
                'current_category': len(formatted_target_question) > 0 and formatted_target_question[0]['category'],
            })
        except Exception:
            abort(422)

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    # get all of the question of a specific category (including pagination)
    def search_questions_by_category(category_id):
        try:
            # select category questions
            target_category = Category.query.filter(
                Category.id == category_id).one_or_none()
            if target_category is None:
                raise NotFound

            questions = Question.query.filter(
                Question.category == target_category.id).all()

            # pagination
            page = request.args.get('page', 1, type=int)
            start = (page-1) * 10
            end = page * 10
            formatted_questions = [question.format() for question in questions]
            return jsonify({
                'success': True,
                'questions': formatted_questions[start:end],
                'total_questions': len(formatted_questions),
                'current_category': target_category.id
            })
        except NotFound:
            abort(404)
        except Exception:
            abort(422)

    @app.route('/play/quizzes', methods=['POST'])
    # find next question
    def get_next_quesetion():
        try:
            body = request.get_json()
            pre_question = body.get('previous_questions', [])
            quiz_category = body.get('quiz_category', None)

            filter_conditions = [Question.id.notin_(pre_question)]

            select_specific_categories = quiz_category['id'] != 0
            if select_specific_categories:
                filter_conditions.append(
                    Question.category == quiz_category['id'])

            unshown_question = Question.query.filter(
                *filter_conditions).first()
            if unshown_question is None:
                raise NoMoreQuestions

            formatted_unshown_question = unshown_question.format()
            return jsonify({
                'success': True,
                'question': formatted_unshown_question
            })
        except NoMoreQuestions:
            # custom exception, return special message to frontend to end the quiz
            return jsonify({
                'success': False,
                'message': 'No More Questions'
            })
        except Exception:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Not Found'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unprocessable'
        }), 422

    @app.errorhandler(400)
    def bad_requeset(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad Request'
        }), 400
    
    @app.errorhandler(405)
    def method_not_found(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'Method Not Found'
        }), 405
    
    return app
