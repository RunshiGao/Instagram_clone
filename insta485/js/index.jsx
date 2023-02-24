import React from 'react';
import PropTypes from 'prop-types';
import InfiniteScroll from 'react-infinite-scroll-component';
import Post from './post';

class Index extends React.Component {
  constructor(props) {
    super(props);
    this.state = { next: '', results: [], url: '' };
    this.nextFetch = this.nextFetch.bind(this);
  }

  componentDidMount() {
    const perfEntries = performance.getEntriesByType('navigation');
    if (perfEntries[0].type === 'back_forward') { // check navigation type
      const { results, next, url } = window.history.state;
      this.setState({
        next,
        results,
        url,
      });
      return;
    }

    const { url } = this.props;
    fetch(url, { credentials: 'same-origin' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        this.setState({
          next: data.next,
          results: data.results,
          url: data.url,
        });
      })
      .catch((error) => console.log(error));
  }

  nextFetch() {
    // Store history before next is fetched.
    window.history.replaceState(this.state, '');
    const { next } = this.state;
    fetch(next, { credentials: 'same-origin' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        const { results } = this.state;
        this.setState({
          next: data.next,
          results: results.concat(data.results),
          url: data.url,
        });
      })
      .catch((error) => console.log(error));
  }

  render() {
    const { results } = this.state;
    const { next } = this.state;
    return (
      <div>
        <InfiniteScroll
          dataLength={results.length}
          next={this.nextFetch}
          hasMore={next !== ''}
          results={results}
          link={next}
        >
          <div>
            {results.map((result) => (
              <Post key={result.postid} url={result.url} />
            ))}
          </div>
        </InfiniteScroll>
      </div>
    );
  }
}

Index.propTypes = {
  url: PropTypes.string.isRequired,
};

export default Index;
