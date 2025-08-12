export const extractCode = (markdown) => {
  const codeBlocks = [];
  const codeRegex = /```(\w+)?\n([\s\S]*?)```/g;
  let match;
  while ((match = codeRegex.exec(markdown)) !== null) {
    codeBlocks.push({
      type: 'code',
      language: match[1] || 'text',
      content: match[2],
    });
  }
  return codeBlocks;
};
