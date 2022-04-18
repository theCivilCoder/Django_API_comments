import io, json
from multiprocessing.dummy import current_process
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from comments_api.models import Comment
from comments_api.serializers import CommentSerializer

from django.db import connection

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

"""
Method will be used once to create a user for testing the basic authentication
"""
def createUser():
    User.objects.create_user("testUser2", "zhuyj@ucalgary.ca", "password2")


"""
Authenticates the user by checking the username and password saved in the request header.
Returns True if registered user is found.
Returns False if registered user is not found.
"""
def isValidUser(request):
    username = request.META['HTTP_USERNAME']
    password = request.META['HTTP_PASSWORD']

    user = authenticate(username=username, password=password)

    if user == None:
        return False
    return True


# Create your views here.
class CommentsView(APIView):
    username = "testUser"
    password = "password"

    # """
    # Get all comments from the database table
    # """
    # def get(self, request, *args, **kwargs):
    #     qs = Comment.objects.all()
    #     print("\n qs = ")
    #     print(qs)
    #     print("\n connection.queries = ")
    #     print(connection.queries)
    #     serializer = CommentSerializer(qs, many=True)
    #     print("\n serializer.data = ")
    #     print(serializer.data)
    #     return Response(serializer.data)

    """
    Get one comment and all of its replies
    """
    def get(self, request, *args, **kwargs):
        # #Uncomment out below to create the User used for Basic Authentication
        # createUser()

        # #Testing authentication without any changes to the database table
        # isAuthenticated = isValidUser(request)
        # if isAuthenticated == False:
        #     return Response(["Failed to authenticate"])
        
        # list stores the comment and all coresponding replies        
        all_comments = []

        # Get the first comment based on id from api call
        current_comment_id = request.GET.get('id')
        if (current_comment_id == None):
            return Response(all_comments)

        qs = Comment.objects.raw(
                "SELECT * FROM comments_api_comment WHERE id=" + current_comment_id)
        serializer = CommentSerializer(qs, many=True)
        all_comments += serializer.data

        # Get all the replies
        while (current_comment_id):
            qs = Comment.objects.raw(
                "SELECT * FROM comments_api_comment WHERE parent_id=" + str(current_comment_id))
            serializer = CommentSerializer(qs, many=True)

            # if no more replies found
            if len(serializer.data) == 0:
                break

            all_comments += serializer.data
            current_comment_id = serializer.data[0]['id']
        
        return Response(all_comments)

    """
    Save a comment which can be a brand new comment (parent_id=0) or a reply (parent_id is not 0) 
    """
    def post(self, request, *args, **kwargs):
        # Check if valid username and password are included in the request header
        isAuthenticated = isValidUser(request)
        if isAuthenticated == False:
            return Response(["Failed to authenticate"])

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    """
    Delete a comment based on an id
    """
    def delete(self, request):
        # Check if valid username and password are included in the request header
        isAuthenticated = isValidUser(request)
        if isAuthenticated == False:
            return Response(["Failed to authenticate"])

        stream = io.BytesIO(request.body)
        data = JSONParser().parse(stream)

        # default error message
        res = {'msg':'Comment with this id does not exist'}
        current_id = data.get('id',None)

        try:    
            comment = Comment.objects.get(id=current_id)
            comment.delete()
            res = {'msg':'Comment with this id was deleted.'}
        except Exception as e:
            #Failed to find an object given the id included in the request body
            print(f"Error: api.views -> delete(): {e}")

        json_data = JSONRenderer().render(res)
        return Response(json_data, content_type='application/json')

    """
    Update a comment based on the id
    """
    def put(self, request):
        # Check if valid username and password are included in the request header
        isAuthenticated = isValidUser(request)
        if isAuthenticated == False:
            return Response(["Failed to authenticate"])

        # default error message
        res = {'msg':'Comment with this id does not exist'}

        try:
            saved_comment = Comment.objects.get(id=request.data['id'])

            saved_comment.text = request.data['text']
            saved_comment.save()
            res = {'msg':'Comment with this id was updated.'}

        except Exception as e:
            #Failed to find an object given the id included in the request body
            print(f"Error: api.views -> put(): {e}")


        json_data = JSONRenderer().render(res)
        return Response(json_data, content_type='application/json')

