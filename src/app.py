
from flask import Flask, request, jsonify, Response
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import json_util
from bson.objectid import ObjectId 
from pickle import load
import pandas as pd

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb+srv://admin:Clave1234@cluster0.fjwgb.mongodb.net/testPymongo.test'
mongo = PyMongo(app)

categorical_columns = ['tipo de ruc',
                             'estado civil',
                             'rubro',
                             'morosidad',
                             'historial crediticio',
                            'antigüedad']

numeric_columns = ['cantidad de cuentas',
                         'saldo neto',
                        'tendencia']

response_columns = ['calificación crediticia']

model = load(open('./src/classifier.pkl', 'rb'))
scaler = load(open('./src/scaler.pkl', 'rb'))

@app.route('/users', methods = ['POST'])

def createUser():

    nombres      = request.json['nombres']
    apellidos    = request.json['apellidos']
    celular      = request.json['celular']
    ruc          = request.json['ruc']
    nacionalidad = request.json['nacionalidad']
    email        = request.json['email']
    password     = request.json['password']

    existUsername = nombres and apellidos and celular and ruc and nacionalidad and email and password

    if existUsername:

        hasedPassword = generate_password_hash(password)

        id = mongo.db.user.insert_one(
            { 'nombres'     : nombres ,
             'apellidos'   : apellidos ,
             'celular'     : celular,
             'ruc'         : ruc ,            
             'nacionalidad' : nacionalidad ,
             'email'       : email ,
             'password'   : hasedPassword }
        )

        response = {
            'id': str(id),
            'email': email,
            'password': password
        }

        return response
    
    else:
        return notFound()

@app.route('/users', methods = ['GET'])

def getUsers():
    users = mongo.db.user.find()
    response = json_util.dumps(users)
    
    return Response(response, mimetype = 'application/json') 

@app.route('/users/<id>', methods = ['GET'])

def getUser(id):

    user = mongo.db.user.find_one({'_id': ObjectId(id)})

    _df = pd.DataFrame(user,index=[0])
    _df[numeric_columns] = scaler.transform(_df[numeric_columns])

    _df_dummies = pd.get_dummies(_df[categorical_columns], drop_first=True)
    _df = pd.concat([_df, _df_dummies], axis=1)
    _df.drop(categorical_columns, axis=1, inplace = True)

    prediction = model.predict(_df)
    return jsonify({'prediction': str(list(prediction))})
    #response = json_util.dumps(user)
    #return Response(response, mimetype = 'application/json') 

@app.route('/profiles', methods = ['GET'])

def getProfiles():
    profiles = mongo.db.profiles.find()
    response = json_util.dumps(profiles)
    
    return Response(response, mimetype = 'application/json')  


@app.route('/users/<id>', methods = ['DELETE'])

def deleteUser(id):
    mongo.db.user.delete_one({'_id': ObjectId(id)})
    
    response = jsonify({
        'message': 'user: ' + id + ' was deleted successfully'
    })

    return response

@app.route('/users/<id>', methods = ['PUT'])

def updateUser(id):
    
    nombres      = request.json['nombres']
    apellidos    = request.json['apellidos']
    celular      = request.json['celular']
    ruc          = request.json['ruc']
    nacionalidad = request.json['nacionalidad']
    email        = request.json['email']
    password     = request.json['password']
    
    existUsername = nombres and apellidos and celular and ruc and nacionalidad and email and password

    if existUsername:

        hasedPassword = generate_password_hash(password)

        mongo.db.user.update_one( {'_id': ObjectId(id)}, {
            '$set': {
            'nombres'     : nombres ,
            'apellidos'   : apellidos ,
            'celular'     : celular,
            'ruc'         : ruc ,            
            'nacionalidad' : nacionalidad ,
            'email'       : email ,
            'password'   : hasedPassword
            }

        })

        response = jsonify({
        'message': 'user:  ' + id + ' was updated successfully'
        })

        return response
    
    else:
        return notFound()


@app.errorhandler(404)
def notFound( error = None):
    
    message = jsonify({
        'message': 'Resource Not Found: ' + request.url,
        'status': 404 
    })

    message.status_code = 404

    return message

if __name__ == '__main__':
    app.run( debug = True )