"""REST API for posts."""
import flask
import json

# from utils import *
import insta485
from insta485.api.utils import get_logname
from insta485.api.utils import check_auth
from insta485.api.utils import query_db
from insta485.api.utils import update_db


@insta485.app.route('/api/v1/')
def get_all_api():
    """Return all available REST API"""
    context = {
        "comments": "/api/v1/comments/",
        "likes": "/api/v1/likes/",
        "posts": "/api/v1/posts/",
        "url": "/api/v1/"
    }
    return flask.jsonify(**context)


@insta485.app.route('/api/v1/comments/', methods=['POST'])
def add_one_comment():
    """Add one comment"""
    print("Adding one comment")
    logname = get_logname() or check_auth()
    content = (flask.request.data.decode())
    content = json.loads(content)
    target = "users/" + str(logname) + "/"
    print("target:" + target)
    if not logname:
        return flask.jsonify({"message": "Forbidden", "status_code": 403})
    postid = flask.request.args.get('postid')
    print("postid: " + postid)
    # breakpoint()
    text = content['text']
    update_db(
        'insert into comments (owner, postid, text) \
            values (?, ?, ?);',
        (logname, postid, text,))
    commentid = query_db(
        "SELECT max(commentid) as id from comments", one=True)["id"]
    context = {
        "commentid": commentid,
        "lognameOwnsThis": True,
        "owner": logname,
        "ownerShowUrl": target,
        "text": text,
        "url": "/api/v1/comments/" + str(commentid) + "/"
    }
    return flask.jsonify(**context), 201


@insta485.app.route('/api/v1/comments/<commentid>/', methods=['DELETE'])
def delete_one_comment(commentid):
    """Delete one comment"""
    logname = get_logname() or check_auth()
    owner = query_db(
        'select owner from comments \
            where commentid = ?',
        (commentid,))
    if not owner:
        return flask.jsonify({"message": "Comment does not exist",
                              "status_code": 404}), 404
    if owner[0]['owner'] != logname:
        return flask.jsonify({"message": "Forbidden",
                              "status_code": 403}), 403
    update_db(
        'delete from comments where owner = ? and commentid = ?',
        (logname, commentid,))
    return flask.jsonify({"message": "Comment deleted",
                          "status_code": 204}), 204
