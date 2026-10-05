jest.mock('nodemailer');

describe('mailer', () => {
  const OLD_ENV = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...OLD_ENV };
    delete process.env.SMTP_HOST;
    delete process.env.SMTP_USER;
    delete process.env.SMTP_PASS;
  });

  afterAll(() => {
    process.env = OLD_ENV;
  });

  it('falls back to a console-logging transport when SMTP is not configured', async () => {
    const nodemailer = require('nodemailer');
    const logSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
    const { sendMail } = require('../../utils/mailer');

    await expect(
      sendMail({ to: 'candidate@example.com', subject: 'Hi', text: 'Body text' })
    ).resolves.not.toThrow();

    expect(logSpy).toHaveBeenCalledWith(expect.stringContaining('candidate@example.com'));
    expect(nodemailer.createTransport).not.toHaveBeenCalled();
    logSpy.mockRestore();
  });

  it('uses a real SMTP transport when SMTP env vars are configured', async () => {
    process.env.SMTP_HOST = 'smtp.example.com';
    process.env.SMTP_USER = 'user';
    process.env.SMTP_PASS = 'pass';

    // Require nodemailer in the same tick as mailer.js so both resolve to the
    // same fresh module instance from the registry (post-resetModules).
    const nodemailer = require('nodemailer');
    const sendMailMock = jest.fn().mockResolvedValue({ accepted: ['candidate@example.com'] });
    nodemailer.createTransport.mockReturnValue({ sendMail: sendMailMock });

    const { sendMail } = require('../../utils/mailer');
    await sendMail({ to: 'candidate@example.com', subject: 'Hi', text: 'Body text' });

    expect(nodemailer.createTransport).toHaveBeenCalledWith(
      expect.objectContaining({ host: 'smtp.example.com' })
    );
    expect(sendMailMock).toHaveBeenCalledWith(
      expect.objectContaining({ to: 'candidate@example.com', subject: 'Hi' })
    );
  });

  it('never throws even if the transport fails', async () => {
    process.env.SMTP_HOST = 'smtp.example.com';
    process.env.SMTP_USER = 'user';
    process.env.SMTP_PASS = 'pass';

    const nodemailer = require('nodemailer');
    const sendMailMock = jest.fn().mockRejectedValue(new Error('SMTP down'));
    nodemailer.createTransport.mockReturnValue({ sendMail: sendMailMock });

    const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const { sendMail } = require('../../utils/mailer');

    await expect(sendMail({ to: 'a@example.com', subject: 'x', text: 'y' })).resolves.toBeUndefined();
    expect(errorSpy).toHaveBeenCalled();
    errorSpy.mockRestore();
  });
});
