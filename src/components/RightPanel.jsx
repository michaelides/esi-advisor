import React from 'react';
import CodeBlock from './artifacts/CodeBlock';
import PlotlyPlot from './artifacts/PlotlyPlot';

const RightPanel = ({ artifacts }) => {
  return (
    <div className="right-panel">
      <h3>Artifacts</h3>
      {artifacts.map((artifact, index) => {
        if (artifact.type === 'code') {
          return <CodeBlock key={index} language={artifact.language} content={artifact.content} />;
        }
        if (artifact.type === 'plot') {
          return <PlotlyPlot key={index} data={artifact.content} />;
        }
        return null;
      })}
    </div>
  );
};

export default RightPanel;
