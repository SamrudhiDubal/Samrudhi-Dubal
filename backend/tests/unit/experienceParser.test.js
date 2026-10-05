const { extractYearsOfExperience, extractEducationLevel } = require('../../utils/experienceParser');

describe('extractYearsOfExperience', () => {
  it('extracts years from "X years of experience" phrasing', () => {
    expect(extractYearsOfExperience('I have 5 years of experience in software engineering.')).toBe(5);
  });

  it('extracts years from "experience of X years" phrasing', () => {
    expect(extractYearsOfExperience('Experience of 8 years in backend development.')).toBe(8);
  });

  it('extracts years from "X+ years in" phrasing', () => {
    expect(extractYearsOfExperience('10+ years in distributed systems.')).toBe(10);
  });

  it('returns the maximum figure when multiple are mentioned', () => {
    const text = '2 years of experience as an intern, then 7 years of experience as a lead engineer.';
    expect(extractYearsOfExperience(text)).toBe(7);
  });

  it('returns null when no years are mentioned', () => {
    expect(extractYearsOfExperience('Passionate software engineer who loves clean code.')).toBeNull();
  });

  it('returns null for empty input', () => {
    expect(extractYearsOfExperience('')).toBeNull();
    expect(extractYearsOfExperience(undefined)).toBeNull();
  });
});

describe('extractEducationLevel', () => {
  it('detects a PhD', () => {
    expect(extractEducationLevel('Ph.D. in Computer Science from MIT.')).toBe('phd');
  });

  it('detects a master\'s degree', () => {
    expect(extractEducationLevel('M.Tech in Software Engineering.')).toBe('master');
  });

  it('detects a bachelor\'s degree', () => {
    expect(extractEducationLevel('B.Tech in Computer Science, 2020.')).toBe('bachelor');
  });

  it('returns the highest level when multiple are mentioned', () => {
    expect(extractEducationLevel('B.Tech in CS, followed by an MBA.')).toBe('master');
  });

  it('returns null when no education is mentioned', () => {
    expect(extractEducationLevel('Experienced backend developer skilled in Node.js.')).toBeNull();
  });
});
