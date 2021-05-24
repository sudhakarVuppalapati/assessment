import json
import boto3
from flask_lambda import FlaskLambda
from flask import request, jsonify
from boto3.dynamodb.conditions import Key

app1 = FlaskLambda(__name__)
dynamodb = boto3.resource("dynamodb", region_name="us-west-1")
dynamodb1 = boto3.client("dynamodb")
client = boto3.client('ssm')
TableNameParameter  =  client.get_parameter(Name='TableName',  WithDecryption= False)
TableNamevalue = TableNameParameter.get("Parameter").get("Value")
#print(TableNameParameter.get("Parameter").get("Value"))
TopicArnParameter =  client.get_parameter(Name='TopicArn',  WithDecryption= False)
TopicArnvalue = TopicArnParameter.get("Parameter").get("Value")
#print(TopicArnParameter.get("Parameter").get("Value"))

table = dynamodb.Table(TableNamevalue)
clientSNS = boto3.client('sns')



@app1.route('/announcements', methods=['GET'])
def listAnnouncements():
    if request.method == 'GET':
        error = 0
       
        try :
           key=request.headers["Exclusivestartkey"]    
           print(key)
           stratkey = json.loads(key)
        except:
            error =1 
        if error != 1 :
            response = dynamodb1.scan(TableName = TableNamevalue,Limit=3,ExclusiveStartKey= stratkey)
        else : 
            response = dynamodb1.scan(TableName = TableNamevalue,Limit=3)
        #response = table.query( KeyConditionExpression=Key('title').eq('testannouncement2'), )
        Count = response['Count']
        if Count != 0 :
            data = response['Items']
            print(response)
            print("LastEvaluatedKey details : ")
            try :
              LastEvaluatedKey = response["LastEvaluatedKey"]
            except: 
              error =2  
            #print(json.loads(LastEvaluatedKey))
            counts = dict()
            counts['Items'] = data
            if error != 2 :
                counts['LastEvaluatedKey'] = response["LastEvaluatedKey"]
            return json_response(counts,200)
        else :
            return json_response("No data available",200)

@app1.route('/announcements', methods=['POST'])
def putAnnouncements():
    # print("request.data  : ", request.data)
    json_object = json.loads(request.data)
    title = json_object["title"] 
    description = json_object["description"]
    if not  title.strip():
        return json_response({"message": "announcements title should not be empty"},400)
    if not  description.strip():
        return json_response({"message": "announcements description should not be empty"},400)    
    print(json_object["title"])
    dbResponse = table.put_item( Item= {"title":  title,"description": description,"date":json_object["date"]})
    #dbResponse = dynamodb1.put_item(TableName = TableNamevalue,Item= {"title":  title,"description": description,"date":json_object["date"]})
    dbreturn = dbResponse.get("ResponseMetadata").get("HTTPStatusCode") 
    if dbreturn != 200 :
        return json_response({"message": "please can you check with your data something went worng with DynamoDB insert data"},dbreturn); 
    else : 
        response = clientSNS.publish( TopicArn=TopicArnvalue, Message=request.data,  Subject='test');
        responsecode = response.get("ResponseMetadata").get("HTTPStatusCode")
        print(responsecode)
        if responsecode != 200 :
            return json_response({"message": "please can you check with your data something went worng sending notification to user"},responsecode); 
        else :
            print("success")
    return json_response({"message": "announcements entry created"},201)

def json_response(data, response_code):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}