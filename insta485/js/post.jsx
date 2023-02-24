import React from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';

class Post extends React.Component {
/* Display number of image and post owner of a single post
*/

  constructor(props) {
    // Initialize mutable state
    super(props);
    this.state = {
      imgUrl: '',
      owner: '',
      comments: [],
      timeStamp: '',
      ownerImgUrl: '',
      ownerShowUrl: '',
      postShowUrl: '',
      postid: '',
      likes: '',
      text: '',
    };

    this.render_comment = this.render_comment.bind(this);
    this.render_likes = this.render_likes.bind(this);
    this.post_comment = this.post_comment.bind(this);
    this.delete_comment = this.delete_comment.bind(this);
    this.post_like = this.post_like.bind(this);
    this.updateInputValue = this.updateInputValue.bind(this);
  }

  componentDidMount() {
    // This line automatically assigns this.props.url to the const variable url
    const { url } = this.props;

    // Call REST API to get the post's information
    fetch(url, { credentials: 'same-origin' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        const a = moment.utc(data.created);
        const time = a.fromNow();
        this.setState({
          imgUrl: data.imgUrl,
          owner: data.owner,
          comments: data.comments,
          timeStamp: time,
          ownerImgUrl: data.ownerImgUrl,
          ownerShowUrl: data.ownerShowUrl,
          postShowUrl: data.postShowUrl,
          postid: data.postid,
          likes: data.likes,
          // lognameLikesThis: data.likes.lognameLikesThis,
        });
      })
      .catch((error) => console.log(error));
  }

  delete_comment(id) {
    const { comments } = this.state;
    const url = `/api/v1/comments/${id}/`;
    fetch(url, {
      credentials: 'same-origin',
      method: 'delete',
    })
      .then((response) => {
        console.log(response);
      })
      .catch((error) => console.log(error));
    const newComments = comments.filter((comment) => comment.commentid !== id);
    this.setState({ comments: newComments });
  }

  post_comment(e) {
    e.preventDefault();
    const { text, postid } = this.state;
    console.log(text);
    const url = `/api/v1/comments/?postid=${postid}`;
    fetch(url, {
      credentials: 'same-origin',
      method: 'POST',
      body: JSON.stringify({
        text,
      }),
    })
      .then((res) => res.json())
      .then((res) => {
        console.log(res);
        this.setState((prevState) => ({
          comments: prevState.comments.concat(res),
        }));
      })
      .catch((err) => { console.log(err); });
  }

  post_like() {
    const { postid, likes } = this.state;
    if (likes.lognameLikesThis) {
      return;
    }
    const url = `/api/v1/likes/?postid=${postid}`;
    console.log('liked');
    console.log(url);
    fetch(url, { credentials: 'same-origin', method: 'POST' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        const newLikes = {
          numLikes: likes.numLikes + 1,
          lognameLikesThis: !likes.lognameLikesThis,
          url: data.url,
        };
        this.setState({
          likes: newLikes,
        });
      })
      .catch((error) => console.log(error));
  }

  delete_like(url) {
    console.log('unliked');
    console.log(url);
    fetch(url, { credentials: 'same-origin', method: 'DELETE' })
      .then((res) => { console.log(res); })
      .catch((err) => { console.log(err); });
    this.setState((prevState) => {
      const likes = { ...prevState.likes };
      likes.numLikes -= 1;
      likes.lognameLikesThis = !likes.lognameLikesThis;
      return { likes };
    });
  }

  updateInputValue(e) {
    const val = e.target.value;
    this.setState({
      text: val,
    });
  }

  render_comment() {
    const { comments } = this.state;
    // const currentComment = this.state.comments;
    if (Object.keys(comments).length === 0) {
      return (
        <div className="Comments" />
      );
    }
    const commentLst = comments.map((comment) => {
      if (comment.lognameOwnsThis) {
        return (
          <div className="Comment" key={comment.commentid}>
            <nobr>
              <a href={comment.ownerShowUrl} className="name">{comment.owner}</a>
              {comment.text}
              <button type="button" onClick={() => this.delete_comment(comment.commentid)} className="delete-comment-button">
                Delete
              </button>
            </nobr>
          </div>
        );
      }
      return (
        <div className="Comment" key={comment.commentid}>
          <a href={comment.ownerShowUrl} className="name">{comment.owner}</a>
          {comment.text}
        </div>
      );
    });
    console.log(commentLst);
    return commentLst;
  }

  render_likes() {
    const { likes } = this.state;
    let likeStatus = '';
    if (likes !== '1') {
      likeStatus = `${likes.numLikes} likes`;
    } else {
      likeStatus = `${likes.numLikes} like`;
    }
    return likeStatus;
  }

  render() {
    // This line automatically assigns this.state.imgUrl to the const variable imgUrl
    // and this.state.owner to the const variable owner
    const {
      imgUrl, owner, comments, timeStamp, ownerImgUrl,
      ownerShowUrl, postShowUrl, likes,
    } = this.state;
    // const comments = this.state.comments;
    // Render number of post image and post owner
    const commentsRendered = this.render_comment(comments);
    const likesRendered = this.render_likes(likes);
    // const humanReadableDate = timeStamp.toTimeString();
    const humanReadableDate = timeStamp;
    let likeButton;
    if (likes.lognameLikesThis) {
      likeButton = (
        <button type="submit" onClick={() => this.delete_like(likes.url)} className="like-unlike-button">
          unlike
        </button>
      );
    } else {
      likeButton = (
        <button type="submit" onClick={() => this.post_like()} className="like-unlike-button">
          like
        </button>
      );
    }
    const { text } = this.state;
    return (
      <div className="post">
        <div>
          <img className="avatar" src={ownerImgUrl} alt="ownerPicture" />
          <a href={ownerShowUrl} className="name">{owner}</a>
          <a href={postShowUrl} className="timestamp">{humanReadableDate}</a>
        </div>
        <img onDoubleClick={this.post_like} className="pic" src={imgUrl} alt="Post" />
        <p>
          {likesRendered}
        </p>
        <div>
          {likeButton}
        </div>
        <div className="CommentSection">
          {commentsRendered}
        </div>
        {/* comment section */}
        <div>
          <div className="CommentBox">
            <form className="comment-form" onSubmit={(e) => this.post_comment(e)}>
              <input type="text" value={text} onChange={this.updateInputValue} />
            </form>
          </div>
        </div>
      </div>
    );
  }
}

Post.propTypes = {
  url: PropTypes.string.isRequired,
};

export default Post;
