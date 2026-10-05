describe('semanticMatcher', () => {
  const OLD_ENV = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...OLD_ENV };
  });

  afterAll(() => {
    process.env = OLD_ENV;
  });

  it('returns null when ANTHROPIC_API_KEY is not configured (no network call)', async () => {
    delete process.env.ANTHROPIC_API_KEY;
    const { getSemanticMatch } = require('../../utils/semanticMatcher');

    const result = await getSemanticMatch('Some resume text', { title: 'Engineer' });
    expect(result).toBeNull();
  });

  it('parses a valid JSON response into a score and summary', async () => {
    process.env.ANTHROPIC_API_KEY = 'test-key';

    jest.doMock('@anthropic-ai/sdk', () => {
      return jest.fn().mockImplementation(() => ({
        messages: {
          create: jest.fn().mockResolvedValue({
            content: [{ type: 'text', text: '{"score": 82, "summary": "Strong fit."}' }],
          }),
        },
      }));
    });

    const { getSemanticMatch } = require('../../utils/semanticMatcher');
    const result = await getSemanticMatch('Resume text', { title: 'Engineer' });

    expect(result).toEqual({ score: 82, summary: 'Strong fit.' });
  });

  it('returns null and does not throw when the API call fails', async () => {
    process.env.ANTHROPIC_API_KEY = 'test-key';

    jest.doMock('@anthropic-ai/sdk', () => {
      return jest.fn().mockImplementation(() => ({
        messages: {
          create: jest.fn().mockRejectedValue(new Error('network error')),
        },
      }));
    });

    const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const { getSemanticMatch } = require('../../utils/semanticMatcher');
    const result = await getSemanticMatch('Resume text', { title: 'Engineer' });

    expect(result).toBeNull();
    errorSpy.mockRestore();
  });

  it('returns null when the response is not parseable JSON', async () => {
    process.env.ANTHROPIC_API_KEY = 'test-key';

    jest.doMock('@anthropic-ai/sdk', () => {
      return jest.fn().mockImplementation(() => ({
        messages: {
          create: jest.fn().mockResolvedValue({
            content: [{ type: 'text', text: 'Sorry, I cannot help with that.' }],
          }),
        },
      }));
    });

    const { getSemanticMatch } = require('../../utils/semanticMatcher');
    const result = await getSemanticMatch('Resume text', { title: 'Engineer' });

    expect(result).toBeNull();
  });
});
