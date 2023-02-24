"""REST API for posts."""
import flask

import insta485
from insta485.api.utils import query_db, get_logname, check_auth

Error400 = {
    'message': 'Bad Request',
    'status_code': 400
}

Error403 = {
    'message': 'Forbidden',
    'status_code': 403
}

Error404 = {
    'message': 'Not Found',
    'status_code': 404
}


@insta485.app.route('/api/v1/posts/')
def get_posts():
    """Return paginated posts."""
    logname = get_logname() or check_auth()
    if not logname:
        return flask.jsonify(**Error403), 403

    size = flask.request.args.get('size', default=10, type=int)
    page = flask.request.args.get('page', default=0, type=int)
    offset = size * page
    if size < 0 or page < 0:
        return flask.jsonify(**Error400), 400

    lte = flask.request.args.get('postid_lte', type=int)
    if not lte:
        max_id = query_db("select max(postid) as max from posts", one=True)
        lte = max_id['max']
        posts = query_db("select distinct postid, owner "
                         "from posts "
                         "left outer join following f on f.username2 = owner "
                         "where owner = ? or f.username1 = ? "
                         "order by postid desc "
                         "limit ? offset ?",
                         (logname, logname, size, offset)
                         )
    else:
        posts = query_db("select distinct postid, owner "
                         "from posts "
                         "left outer join following f on f.username2 = owner "
                         "where (owner = ? or f.username1 = ?) and postid <= ? "
                         "order by postid desc "
                         "limit ? offset ?",
                         (logname, logname, lte, size, offset)
                         )

    results = []
    for post in posts:
        result = {
            'postid': post['postid'],
            'url': f'/api/v1/posts/{post["postid"]}/',
        }
        results.append(result)

    url = flask.request.path if len(
        flask.request.args) == 0 else flask.request.full_path

    if len(posts) < size:
        next_url = ""
    else:
        next_url = (flask.request.path + '?size=' + str(size) + '&page='
                    + str(page + 1) + '&postid_lte=' + str(lte))

    context = {
        'next': next_url,
        'results': results,
        'url': url,
    }
    return flask.jsonify(**context)


@insta485.app.route('/api/v1/posts/<int:postid_url_slug>/')
def get_post(postid_url_slug):
    """Return post on postid."""
    logname = get_logname() or check_auth()
    if not logname:
        return flask.jsonify(**Error403), 403

    postid = postid_url_slug

    # db query
    post = query_db('select * from posts where postid = ?',
                    (postid,), one=True)
    if not post:
        return flask.jsonify(**Error404), 404

    owner = query_db('select * from users where username = ?',
                     (post['owner'],), one=True)
    comments = query_db(
        'select commentid, owner, text from comments where postid = ?;',
        (postid,))
    like = query_db(
        'select count(likeid) numLikes from likes where postid = ? ', (postid,),
        one=True)
    lognameLikesThis = query_db(
        'select likeid from likes where postid = ? and owner = ?;',
        (postid, logname,), one=True)

    for comment in comments:
        """ Comment example.

        {
          "commentid": 2,
          "lognameOwnsThis": false,
          "owner": "jflinn",
          "ownerShowUrl": "/users/jflinn/",
          "text": "I <3 chickens",
          "url": "/api/v1/comments/2/"
        }
        """
        lognameOwnsThis = query_db(
            'select commentid from comments where owner = ? and commentid = ?',
            (logname, comment['commentid'],), one=True)
        comment['lognameOwnsThis'] = True if lognameOwnsThis else False
        comment['ownerShowUrl'] = f'/users/{comment["owner"]}/'
        comment['url'] = f'/api/v1/comments/{comment["commentid"]}/'

    likes = {
        'lognameLikesThis': True if lognameLikesThis else False,
        'numLikes': like['numLikes'],
        'url': f'/api/v1/likes/{lognameLikesThis["likeid"]}/'
        if lognameLikesThis else None,
    }

    context = {
        "created": post['created'],
        "imgUrl": f'/uploads/{post["filename"]}',
        "owner": post['owner'],
        "ownerImgUrl": f'/uploads/{owner["filename"]}',
        "ownerShowUrl": f"/users/{post['owner']}/",
        "postShowUrl": f"/posts/{postid}/",
        "postid": postid,
        "url": flask.request.path,
        "comments": comments,
        "likes": likes,
    }
    return flask.jsonify(**context)
