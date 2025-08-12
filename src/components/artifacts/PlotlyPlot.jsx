import React from 'react';
import Plot from 'react-plotly.js';

const PlotlyPlot = ({ data }) => {
  return (
    <div className="plot-container">
      <Plot
        data={data.data}
        layout={data.layout}
        config={{ responsive: true }}
      />
    </div>
  );
};

export default PlotlyPlot;
