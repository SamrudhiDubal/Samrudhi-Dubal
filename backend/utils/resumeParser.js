const fs = require('fs');
const path = require('path');
const pdfParse = require('pdf-parse');
const mammoth = require('mammoth');

/**
 * Extract raw text from an uploaded resume file (.pdf, .docx, .doc, .txt).
 * @param {string} filePath absolute path to the stored file
 * @returns {Promise<string>} extracted plain text
 */
async function extractResumeText(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const buffer = fs.readFileSync(filePath);

  if (ext === '.pdf') {
    const data = await pdfParse(buffer);
    return data.text || '';
  }

  if (ext === '.docx') {
    const result = await mammoth.extractRawText({ buffer });
    return result.value || '';
  }

  if (ext === '.txt' || ext === '.doc') {
    return buffer.toString('utf-8');
  }

  throw new Error(`Unsupported file type for parsing: ${ext}`);
}

module.exports = { extractResumeText };
