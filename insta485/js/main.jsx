import React from 'react';
import ReactDOM from 'react-dom';
import Index from './index';

ReactDOM.render(
  <Index url="/api/v1/posts/" />,
  document.getElementById('reactEntry'),
);
