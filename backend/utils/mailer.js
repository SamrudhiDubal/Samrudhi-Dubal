// Email notifications. Uses nodemailer with real SMTP credentials when
// configured (SMTP_HOST/SMTP_USER/SMTP_PASS in .env); otherwise falls back
// to logging the email to the console so the app works out of the box in
// development without requiring a mail provider.
const nodemailer = require('nodemailer');

let transporter = null;

function getTransporter() {
  if (transporter) return transporter;

  if (process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS) {
    transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST,
      port: Number(process.env.SMTP_PORT) || 587,
      secure: process.env.SMTP_SECURE === 'true',
      auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
    });
  } else {
    // Dev fallback: log-only "transport" with the same sendMail interface.
    transporter = {
      sendMail: async (options) => {
        console.log('\n--- Email notification (SMTP not configured, logging only) ---');
        console.log(`To: ${options.to}`);
        console.log(`Subject: ${options.subject}`);
        console.log(options.text);
        console.log('--- end email ---\n');
        return { accepted: [options.to] };
      },
    };
  }

  return transporter;
}

/**
 * Send an email. Never throws — notification failures must not break the
 * request that triggered them; errors are logged instead.
 */
async function sendMail({ to, subject, text, html }) {
  if (!to) return;
  try {
    await getTransporter().sendMail({
      from: process.env.SMTP_FROM || 'JobMatch AI <notifications@jobmatch.ai>',
      to,
      subject,
      text,
      html,
    });
  } catch (err) {
    console.error(`Failed to send email to ${to}:`, err.message);
  }
}

async function notifyNewApplicant({ employerEmail, employerName, job, candidateName, matchScore }) {
  await sendMail({
    to: employerEmail,
    subject: `New applicant for ${job.title}: ${candidateName} (${matchScore}% AI match)`,
    text:
      `Hi ${employerName},\n\n` +
      `${candidateName} just applied to your job posting "${job.title}".\n` +
      `AI match score: ${matchScore}%\n\n` +
      `View the ranked applicant list in your employer dashboard to see the full skill breakdown.\n\n` +
      `— JobMatch AI`,
  });
}

async function notifyApplicationSubmitted({ candidateEmail, candidateName, job, matchScore }) {
  await sendMail({
    to: candidateEmail,
    subject: `Application submitted: ${job.title} at ${job.company}`,
    text:
      `Hi ${candidateName},\n\n` +
      `Your application for "${job.title}" at ${job.company} was submitted successfully.\n` +
      `Your AI match score for this role: ${matchScore}%\n\n` +
      `You can track its status anytime from "My Applications".\n\n` +
      `— JobMatch AI`,
  });
}

async function notifyApplicationStatusChange({ candidateEmail, candidateName, job, status }) {
  const friendly = {
    shortlisted: 'shortlisted for the next step',
    rejected: 'not selected to move forward',
    hired: 'selected — congratulations!',
    applied: 'received and is under review',
  };
  await sendMail({
    to: candidateEmail,
    subject: `Update on your application: ${job.title} at ${job.company}`,
    text:
      `Hi ${candidateName},\n\n` +
      `Your application for "${job.title}" at ${job.company} has been ${friendly[status] || status}.\n\n` +
      `— JobMatch AI`,
  });
}

module.exports = {
  sendMail,
  notifyNewApplicant,
  notifyApplicationSubmitted,
  notifyApplicationStatusChange,
};
