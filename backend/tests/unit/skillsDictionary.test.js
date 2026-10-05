const { extractSkills } = require('../../utils/skillsDictionary');
const { toCanonicalSkill } = require('../../utils/skillAliases');

describe('extractSkills', () => {
  it('detects dictionary skills directly', () => {
    const skills = extractSkills('Experienced with React, MongoDB and Docker.');
    // "react" canonicalizes to "react.js", matching the "node.js"/"vue.js" naming convention.
    expect(skills).toEqual(expect.arrayContaining(['react.js', 'mongodb', 'docker']));
    expect(new Set(skills).size).toBe(skills.length); // no duplicates
  });

  it('resolves aliases to canonical skill names', () => {
    const skills = extractSkills('Strong background in JS and K8s deployments, also know GCP.');
    expect(skills).toEqual(expect.arrayContaining(['javascript', 'kubernetes', 'google cloud']));
  });

  it('returns an empty array for empty/undefined input', () => {
    expect(extractSkills('')).toEqual([]);
    expect(extractSkills(undefined)).toEqual([]);
  });

  it('does not false-positive match substrings across word boundaries', () => {
    // "go" is a skill alias for golang; "going" should not match it.
    const skills = extractSkills('We are going to the market to buy mangoes.');
    expect(skills).not.toEqual(expect.arrayContaining(['golang']));
  });
});

describe('toCanonicalSkill', () => {
  it('maps known aliases to their canonical form', () => {
    expect(toCanonicalSkill('js')).toBe('javascript');
    expect(toCanonicalSkill('k8s')).toBe('kubernetes');
    expect(toCanonicalSkill('node')).toBe('node.js');
  });

  it('passes through unknown terms unchanged (lowercased)', () => {
    expect(toCanonicalSkill('Photoshop')).toBe('photoshop');
  });
});
