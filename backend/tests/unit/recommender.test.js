const {
  buildCandidateProfileText,
  recommendJobsForCandidate,
  matchCandidatesForJob,
} = require('../../utils/recommender');

const reactJob = {
  _id: 'job-react',
  title: 'Frontend Developer',
  description: 'Build React user interfaces with JavaScript and CSS.',
  skillsRequired: ['react', 'javascript', 'css'],
  experienceLevel: 'entry',
};

const mlJob = {
  _id: 'job-ml',
  title: 'Machine Learning Engineer',
  description: 'Train machine learning models in Python with TensorFlow and pandas.',
  skillsRequired: ['python', 'tensorflow', 'pandas'],
  experienceLevel: 'mid',
};

const frontendCandidate = {
  _id: 'c-frontend',
  name: 'Fiona',
  title: 'Frontend developer',
  skills: ['react', 'javascript'],
  resumeText: 'Frontend developer with 3 years of experience in React, JavaScript and CSS.',
};

const mlCandidate = {
  _id: 'c-ml',
  name: 'Manoj',
  skills: ['python'],
  resumeText: 'Data scientist, 4 years of experience with Python, TensorFlow, pandas, machine learning.',
};

describe('buildCandidateProfileText', () => {
  it('prefers the saved resume text', () => {
    expect(buildCandidateProfileText(frontendCandidate)).toBe(frontendCandidate.resumeText);
  });

  it('falls back to headline, bio and skills when there is no resume', () => {
    const text = buildCandidateProfileText({
      title: 'Backend engineer',
      bio: 'I like APIs',
      skills: ['node.js', 'mongodb'],
    });
    expect(text).toContain('Backend engineer');
    expect(text).toContain('I like APIs');
    expect(text).toContain('mongodb');
  });

  it('returns an empty string for an empty profile', () => {
    expect(buildCandidateProfileText({})).toBe('');
  });
});

describe('recommendJobsForCandidate', () => {
  it('ranks the best-fitting job first', () => {
    const recs = recommendJobsForCandidate(frontendCandidate, [mlJob, reactJob]);
    expect(recs.map((r) => r.job._id)).toEqual(['job-react', 'job-ml']);
    expect(recs[0].match.matchScore).toBeGreaterThan(recs[1].match.matchScore);
    expect(recs[0].match.missingSkills).toEqual([]);
  });

  it('respects limit and minScore', () => {
    expect(recommendJobsForCandidate(frontendCandidate, [mlJob, reactJob], { limit: 1 })).toHaveLength(1);
    const strict = recommendJobsForCandidate(frontendCandidate, [mlJob, reactJob], { minScore: 60 });
    expect(strict.map((r) => r.job._id)).toEqual(['job-react']);
  });
});

describe('matchCandidatesForJob', () => {
  it('ranks candidates by fit for the job', () => {
    const matches = matchCandidatesForJob(mlJob, [frontendCandidate, mlCandidate]);
    expect(matches[0].candidate._id).toBe('c-ml');
    expect(matches[0].match.missingSkills).toEqual([]);
  });

  it('skips candidates with nothing to match on', () => {
    const matches = matchCandidatesForJob(reactJob, [{ _id: 'empty', skills: [] }, frontendCandidate]);
    expect(matches.map((m) => m.candidate._id)).toEqual(['c-frontend']);
  });
});
