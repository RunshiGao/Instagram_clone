"""REST API for likes."""
import flask
import insta485
from insta485.api.utils import query_db, update_db, get_logname, check_auth

Error403 = {
    'message': 'The user does not own the like',
    'status_code': 403
}

Error404 = {
    'message': 'likeid does not exist',
    'status_code': 404
}


@insta485.app.route('/api/v1/likes/', methods=['POST'])
def add_likes():
    """Add likes"""
    logname = get_logname() or check_auth()
    if not logname:
        return flask.jsonify(**Error403), 403
    postid = flask.request.args.get('postid')

    # ?????
    # like = query_db(
    #     """SELECT likeid, count(likeid) numLikes FROM likes WHERE postid = ?;""", (postid,),
    #     one=True)
    # lognameLikesThis = query_db(
    #     """SELECT likeid FROM likes WHERE postid = ? and owner = ?;""",
    #     (postid, logname,))
    #
    # if lognameLikesThis:
    #     context = {
    #         "likeid": like["likeid"],
    #         "url": "/api/v1/likes/" + str(like["likeid"]) + "/",
    #     }
    #     return flask.jsonify(**context), 200
    #
    # update_db("""INSERT INTO likes(owner, postid) VALUES (?, ?);""",
    #           (logname, postid,))
    # context = {
    #     "lognameLikesThis": lognameLikesThis,
    #     "numLikes": like['numLikes'],
    #     "url": "/api/v1/likes/" + str(like["likeid"]) + "/",
    # }

    lognameLikesThis = query_db(
        """SELECT likeid FROM likes WHERE postid = ? and owner = ?;""",
        (postid, logname,), one=True)

    if lognameLikesThis:
        context = {
            # "lognameLikesThis": True,
            "likeid": lognameLikesThis["likeid"],
            "url": "/api/v1/likes/" + str(lognameLikesThis["likeid"]) + "/",
        }
        return flask.jsonify(**context), 200

    update_db("""INSERT INTO likes(owner, postid) VALUES (?, ?);""",
              (logname, postid,))

    like = query_db(
        """SELECT likeid FROM likes WHERE postid = ? and owner = ?;""",
        (postid, logname,), one=True)
    context = {
        "likeid": like["likeid"],
        "url": "/api/v1/likes/" + str(like["likeid"]) + "/",
    }

    return flask.jsonify(**context), 201


@insta485.app.route('/api/v1/likes/<likeid>/', methods=['DELETE'])
def delete_like(likeid):
    """Delete a like"""
    logname = get_logname() or check_auth()
    if not logname:
        return flask.jsonify(**Error403), 403
    owner = query_db("""SELECT owner FROM likes WHERE likeid=?""", (likeid,))
    print(owner)
    print(logname)
    if not owner:
        return flask.jsonify(**Error404), 404
    if owner[0]['owner'] != logname:
        return flask.jsonify(**Error403), 403

    update_db("""DELETE FROM likes WHERE owner = ? and likeid = ? """,
              (logname, likeid,))

    return flask.jsonify({"message": "like deleted",
                          "status_code": 204}), 204
