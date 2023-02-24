"""
Insta485 index (main) view.

URLs include:
/
"""

import hashlib
import logging
import os
import pathlib
import sqlite3
import uuid

import arrow
import flask

import insta485


def encrypt_new_password(password):
    """Generate the encrypted password from the new password."""
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def encrypt_with_salt_password(password, salt):
    """Generate the encrypted password with the salt."""
    algorithm = 'sha512'
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    return password_hash


def check_password(password, password_db_string):
    """Check the validation of the password."""
    [algorithm, salt, password_hash] = password_db_string.split("$")
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    return hash_obj.hexdigest() == password_hash


def get_logname():
    """Check if user log in and return logname."""
    if 'username' not in flask.session:
        return None
    logname = flask.session['username']
    return logname


def update_db(operation, args=()):
    """Update db record."""
    try:
        insta485.model.get_db().execute(operation, args)
        insta485.model.close_db(None)
    except sqlite3.Error as err:
        logging.error(msg="DB UPDATE FAILED", exc_info=err)


def query_db(query, args=(), one=False):
    """Perform db query."""
    cur = insta485.model.get_db().execute(query, args)
    res = cur.fetchall()
    insta485.model.close_db(None)
    return (res[0] if res else None) if one else res


def save_file(fileobj):
    """Save the file, modified from spec."""
    filename = fileobj.filename
    # Compute base name (filename without directory).  We use a UUID to avoid
    # clashes with existing files, and ensure that the name is compatible
    # with the filesystem.
    stem = uuid.uuid4().hex
    suffix = pathlib.Path(filename).suffix
    uuid_basename = f"{stem}{suffix}"
    # Save to disk
    path = insta485.app.config["UPLOAD_FOLDER"] / uuid_basename
    fileobj.save(path)
    # return the uuid
    return uuid_basename


@insta485.app.route('/likes/', methods=['POST'])
def create_like():
    """Operate a like."""
    target = flask.request.args.get('target')
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))
    operation = flask.request.form.get('operation')
    postid = flask.request.form.get('postid')
    record_exist = query_db(
        'select likeid from likes where owner = ? and postid = ?;',
        (logname, postid,),
        one=True)
    if operation == 'like' and not record_exist:
        update_db('insert into likes(owner, postid) values (?, ?);',
                  (logname, postid,))
    elif operation == 'unlike' and record_exist:
        update_db('delete from likes where owner = ? and postid = ?;',
                  (logname, postid,))
    else:
        return flask.abort(409)
    return flask.redirect(target) if target else flask.redirect('/')


@insta485.app.route('/following/', methods=['POST'])
def create_following():
    """Operate a following."""
    target = flask.request.args.get('target')
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))
    operation = flask.request.form.get('operation')
    username = flask.request.form.get('username')
    isfollow = query_db(
        'select * from following where username1 = ? AND username2 = ?',
        (logname, username,))
    print(isfollow)
    if operation == 'follow':
        if isfollow:
            flask.abort(409)
        update_db('insert into following (username1, username2) '
                  'values (?, ?);',
                  (logname, username,))
    else:
        if not isfollow:
            flask.abort(409)
        update_db(
            'delete from following where username1 = ? and username2 = ?;',
            (logname, username,))
    return flask.redirect(target) if target else flask.redirect('/')


@insta485.app.route('/comments/', methods=['POST'])
def create_comments():
    """Operate a comment."""
    target = flask.request.args.get('target')
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))
    operation = flask.request.form.get('operation')
    postid = flask.request.form.get('postid')
    text = flask.request.form.get('text')
    commentid = flask.request.form.get('commentid')

    if operation == 'create':
        if text == '' or not text:
            flask.abort(400)
        update_db(
            'insert into comments (owner, postid, text) values (?, ?, ?);',
            (logname, postid, text,))
    elif operation == 'delete':
        # cannot delete when post.owner != logname
        logname_is_owner = query_db(
            'select commentid from comments where owner = ? and commentid = ?',
            (logname, commentid,))
        if not logname_is_owner:
            flask.abort(403)
        update_db(
            'delete from comments where owner = ? and commentid = ?',
            (logname, commentid,))

    return flask.redirect(target) if target else flask.redirect('/')


@insta485.app.route('/')
def show_index():
    """Display / route."""
    # Check if the user is logged in
    # flask.session.clear()
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))

    posts = query_db("select distinct postid, filename, owner, p.created "
                     "from posts p "
                     "left outer join following f on f.username2 = owner "
                     "where owner = ? or f.username1 = ? "
                     "order by postid desc;",
                     (logname, logname,)
                     )
    l = query_db("select username from users")
    for post in posts:
        # use arrow tool to deal with timestamp
        post['created'] = arrow.get(post['created']).humanize()

        # db query
        comments = query_db(
            'select * from comments where postid = ?;', (post['postid'],))
        avatar = query_db(
            'select filename from users where username = ?;', (post['owner'],),
            one=True)
        like = query_db(
            'select count(likeid) likes from likes where postid = ?;',
            (post['postid'],), one=True)
        liked_by_user = query_db(
            'select likeid from likes where postid = ? and owner = ?;',
            (post['postid'], logname,))

        # pass to context
        post['comments'] = comments
        post['avatar'] = avatar['filename']
        post['like'] = like['likes']
        post['liked'] = liked_by_user
    return flask.render_template("index.html", logname=logname, posts=posts)


@insta485.app.route('/users/<user_url_slug>/')
def show_user(user_url_slug):
    """Display user page."""
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))

    # db query
    fullname = query_db(
        'select fullname from users where username = ?;', (user_url_slug,),
        one=True)
    if not fullname:
        return flask.abort(404)

    posts = query_db('select * from posts where owner = ?', (user_url_slug,))
    count_posts = query_db(
        'select count(postid) count from posts where owner = ?',
        (user_url_slug,), one=True)
    count_following = query_db(
        "select count(username2) count "
        "from following "
        "where following.username1 == ?",
        (user_url_slug,), one=True
    )
    count_followers = query_db(
        "select count(username1) count "
        "from following "
        "where following.username2 == ?",
        (user_url_slug,), one=True
    )

    is_follow = query_db(
        'select * from following where username1 = ? and username2 = ?',
        (logname, user_url_slug,)
    )

    # pass to context
    user = {'username': user_url_slug,
            'total_posts': count_posts['count'],
            'following': count_following['count'],
            'followers': count_followers['count'],
            'fullname': fullname['fullname']
            }

    return flask.render_template('user.html',
                                 user=user,
                                 logname=logname,
                                 logname_follows_username=is_follow,
                                 posts=posts
                                 )


@insta485.app.route('/explore/')
def show_explore():
    """Display explore page."""
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))
    not_following = query_db(
        "select username from users where username != ? "
        "except "
        "select username2 from users "
        "left join following f on users.username = f.username1 "
        "where username1 = ?;",
        (logname, logname,)
    )
    for user in not_following:
        filename = query_db(
            "select filename from users where username = ?",
            (user['username'],), one=True)
        user['filename'] = filename['filename']
    return flask.render_template('explore.html', not_following=not_following,
                                 logname=logname)


@insta485.app.route('/posts/<postid_url_slug>/')
def show_post(postid_url_slug):
    """Display post page."""
    # Check if the user is logged in
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))
    postid = postid_url_slug

    # db query
    post = query_db('select * from posts where postid = ?',
                    (postid,), one=True)
    post['created'] = arrow.get(post['created']).humanize()
    owner = query_db('select * from users where username = ?',
                     (post['owner'],), one=True)
    comments = query_db('select * from comments where postid = ?;', (postid,))
    like = query_db(
        'select count(likeid) likes from likes where postid = ?;', (postid,),
        one=True)
    liked_by_user = query_db(
        'select likeid from likes where postid = ? and owner = ?;',
        (postid, logname,))

    # pass to context
    post['likes'] = like['likes']
    post['liked'] = liked_by_user
    post['comments'] = comments

    return flask.render_template('post.html', post=post, owner=owner,
                                 logname=logname)


@insta485.app.route('/posts/', methods=['post'])
def create_post():
    """Operate post create and delete."""
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))
    target = flask.request.args.get('target')
    operation = flask.request.form.get('operation')
    if operation == 'create':
        fileobj = flask.request.files["file"]
        if not fileobj or fileobj.filename == '':
            flask.abort(400)
        uuid_name = save_file(fileobj)
        update_db('insert into posts (filename, owner) values (?, ?);',
                  (uuid_name, logname,))
    elif operation == 'delete':
        postid = flask.request.form.get('postid')
        logname_is_owner = query_db(
            'select filename from posts where postid = ? and owner = ?',
            (postid, logname,),
            one=True)
        if not logname_is_owner:
            return flask.abort(403)
        filename = logname_is_owner['filename']
        path = insta485.app.config["UPLOAD_FOLDER"] / filename
        os.remove(path)
        update_db('delete from posts where postid = ?', (postid,))
    return flask.redirect(target) if target else flask.redirect(
        f'/users/{logname}/')


@insta485.app.route('/users/<user_url_slug>/followers/')
def get_followers(user_url_slug):
    """Show followers."""
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))
    query_line = "SELECT username1, filename " \
                 "From users, following " \
                 "where following.username2 = ? " \
                 "AND following.username1 = users.username;"
    results = query_db(query_line, (user_url_slug,))
    if not results:
        return flask.abort(404)
    followers = []
    for rst in results:
        query_line = "SELECT Count(*) " \
                     "FROM following " \
                     "Where following.username1 =? " \
                     "AND following.username2 = ?;"
        name1 = flask.session['username']
        name2 = rst['username1']
        follow_res = query_db(query_line, (name1, name2,))
        status = False
        if follow_res[0]['Count(*)'] > 0:
            print(follow_res)
            status = True
        content = {'username': rst['username1'],
                   'user_img_url': '/uploads/' + rst['filename'],
                   'logname_follows_username': status}
        followers.append(content)
    return flask.render_template("followers.html", username=user_url_slug,
                                 logname=flask.session['username'],
                                 followers=followers)


@insta485.app.route('/users/<user_url_slug>/following/')
def get_following(user_url_slug):
    """Reoute to given user's following page."""
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))
    query_line = "SELECT username2, filename " \
                 "From users, following " \
                 "where following.username1 == ? " \
                 "AND following.username2 = users.username"
    results = query_db(query_line, (user_url_slug,))
    if not results:
        return flask.abort(404)
    following = []
    for rst in results:
        query_line = "SELECT Count(*) " \
                     "From following " \
                     "Where following.username1 =? " \
                     "AND following.username2 = ?"
        follow_res = query_db(query_line,
                              (flask.session['username'], rst['username2'],))
        status = False
        if follow_res[0]['Count(*)'] > 0:
            status = True
        content = {'username': rst['username2'],
                   'user_img_url': '/uploads/' + rst['filename'],
                   'logname_follows_username': status}
        following.append(content)
    return flask.render_template("following.html", username=user_url_slug,
                                 logname=flask.session['username'],
                                 following=following)


@insta485.app.route("/accounts/logout/", methods=['POST'])
def logout():
    """Log out redirection."""
    print("DEBUG Logout:", flask.session['username'])
    flask.session.clear()
    print(flask.Response.location)
    return flask.redirect(flask.url_for('login'))


@insta485.app.route('/accounts/login/')
def login():
    """Routing logic of login page."""
    if 'username' not in flask.session:
        return flask.render_template("login.html", logname="login")
    return flask.redirect(flask.url_for('show_index'))


@insta485.app.route('/accounts/create/')
def create():
    """Create new account."""
    if 'username' not in flask.session:
        return flask.render_template("create.html")
    return flask.redirect(flask.url_for('edit'))


@insta485.app.route('/accounts/edit/')
def edit():
    """Edit user."""
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))

    context = {"logname": flask.session["username"]}
    other = query_db(
        "SELECT fullname, filename AS user_img_url, email "
        "FROM users WHERE username=?",
        (flask.session["username"],), one=True)
    return flask.render_template("edit.html", **context, **other)


@insta485.app.route('/accounts/delete/')
def delete():
    """Delete account."""
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))

    context = {"logname": flask.session["username"]}
    return flask.render_template("delete.html", **context)


@insta485.app.route('/accounts/password/')
def password_operation():
    """Show password page."""
    logname = get_logname()
    if not logname:
        return flask.redirect(flask.url_for('login'))

    context = {"logname": flask.session["username"]}
    return flask.render_template("password.html", **context)


@insta485.app.route('/accounts/', methods=['POST'])
def account_operation_handler():
    """Deal with many account related operations."""
    if flask.request.form.get('operation') == 'login':
        return account_login()
    if flask.request.form.get('operation') == 'create':
        return account_create()
    if flask.request.form.get('operation') == 'delete':
        return account_delete()
    if flask.request.form.get('operation') == 'edit_account':
        return account_edit()
    if flask.request.form.get('operation') == 'update_password':
        return account_password()
    return 0


def account_login():
    """Handle login."""
    redirect_url = flask.request.args.get(
        'target', default=flask.url_for('show_index'), type=str)
    print(redirect_url)

    username = flask.request.form.get('username')
    password = (flask.request.form.get('password'))
    if not username or not password or \
            not username.strip() or not password.strip():
        flask.abort(400)
    result = query_db('SELECT password FROM users WHERE username=?',
                      (username,))
    if not result:
        flask.abort(403)
    _, salt, encrypted_password = result[0]['password'].split('$')
    candidate_password = encrypt_with_salt_password(password, salt)
    if candidate_password != encrypted_password:
        flask.abort(403)
    flask.session['username'] = username
    return flask.redirect(redirect_url)


def account_create():
    """Handle create."""
    username = flask.request.form.get('username')
    password = (flask.request.form.get('password'))
    fullname = (flask.request.form.get('fullname'))
    email = (flask.request.form.get('email'))
    if not username or not password or not fullname or not email:
        flask.abort(400)

    cur = query_db(
        "SELECT COUNT(*) AS num FROM users WHERE username=?",
        (flask.request.form["username"],), one=True)
    if cur['num'] != 0:
        flask.abort(409)
    if "file" in flask.request.files:
        file = flask.request.files["file"]
        filename = file.filename

        # Compute base name
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix
        uuid_basename = f"{stem}{suffix}"

        update_db(
            "INSERT INTO "
            "users(username,fullname,email,filename,password) "
            "VALUES (?,?,?,?,?)",
            (flask.request.form["username"],
             flask.request.form["fullname"],
             flask.request.form["email"],
             uuid_basename,
             encrypt_new_password(flask.request.form["password"]),))
        # Save to disk
        path = insta485.app.config["UPLOAD_FOLDER"] / uuid_basename
        file.save(path)
    else:
        flask.abort(400)

    res = query_db(
        "SELECT password FROM users WHERE username=?",
        (flask.request.form["username"],), one=True)
    if res and check_password(flask.request.form["password"],
                              res['password']):
        flask.session['logged_in'] = True
        flask.session['username'] = flask.request.form["username"]
    else:
        flask.flash('Fail to login!')
        flask.abort(403)
    return flask.redirect(flask.url_for('show_index'))


def account_edit():
    """Handle edit."""
    # if flask.request.method == 'POST':
    redirect_url = flask.request.args.get(
        'target', default=flask.url_for('show_index'), type=str)

    logname = flask.session['username']
    if not logname:
        flask.abort(403)

    update_db("""UPDATE users
        SET fullname=?, email=?
        WHERE username=?""", (
        flask.request.form["fullname"], flask.request.form["email"],
        flask.session["username"],))
    if not flask.request.form.get('fullname') \
            or not flask.request.form.get('email'):
        flask.abort(400)
    if "file" in flask.request.files:
        cur = query_db(
            "SELECT filename FROM users WHERE username=?",
            (flask.session["username"],), one=True)
        filename = cur["filename"]
        path = insta485.app.config["UPLOAD_FOLDER"] / filename

        os.remove(path)

        # Unpack flask object
        fileobj = flask.request.files["file"]
        filename = fileobj.filename

        # Compute base name
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix
        uuid_basename = f"{stem}{suffix}"

        update_db("""UPDATE users
            SET filename=?
            WHERE username=?""",
                  (uuid_basename, flask.session["username"],))

        path = insta485.app.config["UPLOAD_FOLDER"] / uuid_basename
        fileobj.save(path)
    return flask.redirect(redirect_url)


def account_delete():
    """Handle delete."""
    # if flask.request.method == 'POST':
    logname = flask.session['username']
    if not logname:
        flask.abort(403)

    post_files = query_db('select filename from posts where owner = ?',
                          (logname,))
    for file in post_files:
        path = insta485.app.config["UPLOAD_FOLDER"] / file['filename']
        os.remove(path)

    filename = query_db("SELECT filename FROM users WHERE username=?",
                        (logname,), one=True)
    avatar_filename = filename['filename']
    path = os.path.join(
        insta485.app.config["UPLOAD_FOLDER"],
        avatar_filename
    )
    os.remove(path)

    update_db("DELETE FROM users WHERE username=?", (logname,))
    flask.session.pop('username', None)
    return flask.redirect(flask.url_for('create'))


def account_password():
    """Handle update password."""
    # if flask.request.method == 'POST':

    logname = flask.session['username']
    if not logname:
        flask.abort(403)

    cur = query_db(
        "SELECT password FROM users WHERE username=?",
        (flask.session["username"],), one=True)

    password = flask.request.form.get('password')
    new_password1 = flask.request.form.get('new_password1')
    new_password2 = flask.request.form.get('new_password2')
    if not password or not new_password1 or not new_password2:
        flask.abort(400)
    if not check_password(flask.request.form["password"],
                          cur["password"]):
        flask.abort(403)

    if flask.request.form["new_password1"] \
            != flask.request.form["new_password2"]:
        flask.abort(401)

    update_db("UPDATE users SET password=?",
              (encrypt_new_password(
                  flask.request.form["new_password1"]),))

    return flask.redirect(flask.url_for('edit'))


@insta485.app.route("/uploads/<path:filename>")
def send_file(filename):
    """Deal with sending files."""
    logname = get_logname()
    if not logname:
        flask.abort(403)

    filepath = insta485.app.config['UPLOAD_FOLDER'] / filename
    if not os.path.exists(filepath):
        flask.abort(404)

    return flask.send_from_directory(insta485.app.config['UPLOAD_FOLDER'],
                                     filename,
                                     as_attachment=True)
