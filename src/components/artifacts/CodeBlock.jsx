import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { a11yDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const CodeBlock = ({ language, content }) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `code.${language || 'txt'}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="code-block-container">
      <div className="code-block-header">
        <span>{language}</span>
        <div className="code-block-buttons">
          <button onClick={handleCopy}><i className="fa-solid fa-copy"></i> Copy</button>
          <button onClick={handleDownload}><i className="fa-solid fa-download"></i> Download</button>
        </div>
      </div>
      <SyntaxHighlighter language={language} style={a11yDark}>
        {content}
      </SyntaxHighlighter>
    </div>
  );
};

export default CodeBlock;
