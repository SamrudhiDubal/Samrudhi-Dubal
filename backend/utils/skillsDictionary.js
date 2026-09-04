// A curated dictionary of common skills/technologies used to extract
// structured skills from free-form resume text when a candidate has not
// explicitly listed skills. Extend this list as needed.
const SKILLS_DICTIONARY = [
  // Languages
  'javascript', 'typescript', 'python', 'java', 'c++', 'c#', 'c', 'go', 'golang', 'rust',
  'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'dart', 'sql', 'html',
  'css', 'sass', 'less',
  // Frontend
  'react', 'react.js', 'redux', 'vue', 'vue.js', 'angular', 'next.js', 'nextjs', 'nuxt',
  'svelte', 'jquery', 'tailwind', 'tailwindcss', 'bootstrap', 'material-ui', 'webpack',
  'vite', 'babel',
  // Backend
  'node', 'node.js', 'express', 'express.js', 'django', 'flask', 'fastapi', 'spring',
  'spring boot', '.net', 'asp.net', 'laravel', 'ruby on rails', 'rails', 'graphql', 'rest',
  'restful api', 'grpc', 'microservices', 'websocket',
  // Databases
  'mongodb', 'mysql', 'postgresql', 'postgres', 'sqlite', 'redis', 'elasticsearch',
  'cassandra', 'dynamodb', 'firebase', 'oracle', 'mariadb', 'neo4j',
  // Cloud/DevOps
  'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s', 'terraform',
  'jenkins', 'ci/cd', 'ansible', 'linux', 'nginx', 'git', 'github', 'gitlab', 'bitbucket',
  'devops',
  // Data/AI
  'machine learning', 'deep learning', 'nlp', 'natural language processing',
  'computer vision', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
  'data analysis', 'data science', 'data engineering', 'spark', 'hadoop', 'tableau',
  'power bi', 'etl', 'llm', 'generative ai', 'ai',
  // Mobile
  'android', 'ios', 'react native', 'flutter', 'xamarin',
  // Testing
  'jest', 'mocha', 'chai', 'cypress', 'selenium', 'junit', 'pytest', 'testing',
  'test automation', 'qa',
  // Soft/PM
  'agile', 'scrum', 'kanban', 'jira', 'project management', 'product management',
  'leadership', 'communication', 'team management', 'stakeholder management',
  // Design
  'figma', 'sketch', 'adobe xd', 'ui/ux', 'ux design', 'ui design', 'photoshop', 'illustrator',
  // Security
  'cybersecurity', 'penetration testing', 'security', 'oauth', 'jwt',
];

const normalize = (text) => text.toLowerCase();

function extractSkills(text) {
  if (!text) return [];
  const normalized = normalize(text);
  const found = new Set();
  for (const skill of SKILLS_DICTIONARY) {
    const escaped = skill.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const pattern = /^[a-z0-9]/.test(skill)
      ? new RegExp(`(?:^|[^a-z0-9])${escaped}(?:$|[^a-z0-9])`, 'i')
      : new RegExp(escaped, 'i');
    if (pattern.test(normalized)) {
      found.add(skill);
    }
  }
  return Array.from(found);
}

module.exports = { SKILLS_DICTIONARY, extractSkills };
