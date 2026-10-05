const { computeMatchScore } = require('../../utils/aiMatcher');

describe('computeMatchScore', () => {
  const job = {
    title: 'Senior Backend Engineer',
    description:
      'We need a senior engineer experienced with Node.js, Express, MongoDB and REST APIs to build scalable backend services.',
    skillsRequired: ['node.js', 'express', 'mongodb', 'rest'],
    experienceLevel: 'senior',
  };

  it('scores a strong, relevant resume highly', () => {
    const resume =
      'Backend developer with 6 years of professional experience. Skilled in JS, Node, ' +
      'Express.js and MongoDB, building RESTful APIs. B.Tech in Computer Science.';
    const result = computeMatchScore(resume, job);

    expect(result.score).toBeGreaterThanOrEqual(70);
    expect(result.skillMatchPercent).toBe(100);
    expect(result.matchedSkills).toEqual(
      expect.arrayContaining(['node.js', 'express.js', 'mongodb', 'rest'])
    );
    expect(result.missingSkills).toHaveLength(0);
    expect(result.candidateYearsOfExperience).toBe(6);
    expect(result.educationLevel).toBe('bachelor');
  });

  it('scores an irrelevant resume at or near zero', () => {
    const resume =
      'Graphic designer with expertise in Photoshop, Illustrator, and Figma for branding and UI mockups.';
    const result = computeMatchScore(resume, job);

    expect(result.score).toBeLessThan(20);
    expect(result.matchedSkills).toHaveLength(0);
    expect(result.missingSkills).toEqual(
      expect.arrayContaining(['node.js', 'express.js', 'mongodb', 'rest'])
    );
  });

  it('resolves skill aliases to their canonical form (js -> javascript, k8s -> kubernetes)', () => {
    const aliasJob = {
      title: 'Platform Engineer',
      description: 'Deploy and manage containerized workloads.',
      skillsRequired: ['javascript', 'kubernetes'],
      experienceLevel: 'mid',
    };
    const resume = 'Experienced with JS and K8s for container orchestration.';
    const result = computeMatchScore(resume, aliasJob);

    expect(result.matchedSkills).toEqual(expect.arrayContaining(['javascript', 'kubernetes']));
    expect(result.skillMatchPercent).toBe(100);
  });

  it('treats a job with no required skills as a full skill match', () => {
    const openJob = { title: 'Generalist', description: 'Various duties.', skillsRequired: [] };
    const result = computeMatchScore('Some resume text', openJob);
    expect(result.skillMatchPercent).toBe(100);
  });

  it('scores experience fit as null (unknown) when no years are mentioned, redistributing weight', () => {
    const resume = 'Skilled in Node.js, Express, MongoDB and REST API design.';
    const result = computeMatchScore(resume, job);
    expect(result.experienceFitPercent).toBeNull();
    expect(result.score).toBeGreaterThan(0);
  });

  it('includes declared candidate profile skills in the skill match', () => {
    const resume = 'Recently graduated, eager to learn backend development.';
    const result = computeMatchScore(resume, job, ['node.js', 'express', 'mongodb', 'rest']);
    expect(result.skillMatchPercent).toBe(100);
  });
});
