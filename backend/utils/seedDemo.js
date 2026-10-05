// Populates the database with demo users, jobs and AI-scored applications so
// the portal can be demonstrated immediately (e.g. for a project viva).
//
// Re-running is safe: it first removes only the previous demo data (accounts
// whose email ends in @demo.jobmatch and everything they own).
//
// Usage:
//   npm run seed:demo
// All demo accounts use the password: demo1234
require('dotenv').config();
const mongoose = require('mongoose');
const connectDB = require('../config/db');
const User = require('../models/User');
const Job = require('../models/Job');
const Application = require('../models/Application');
const { computeMatchScore } = require('./aiMatcher');

const PASSWORD = 'demo1234';
const DOMAIN = '@demo.jobmatch';

const employers = [
  { key: 'techcorp', name: 'Priya Sharma', company: 'TechCorp Solutions', title: 'HR Manager' },
  { key: 'datawise', name: 'Arjun Mehta', company: 'DataWise Analytics', title: 'Talent Lead' },
];

const candidates = [
  {
    key: 'ananya',
    name: 'Ananya Iyer',
    title: 'Full-Stack Developer',
    skills: ['react', 'node.js', 'mongodb'],
    resumeText: `Ananya Iyer - Full-Stack Developer
B.Tech in Computer Science and Engineering, SRM Institute of Science and Technology.
3 years of experience building MERN stack web applications.
Skills: JavaScript, TypeScript, React, Node.js, Express, MongoDB, REST APIs, Git, Docker, HTML, CSS.
Built a real-time chat app with Socket.io and a job board with JWT authentication.`,
  },
  {
    key: 'rahul',
    name: 'Rahul Verma',
    title: 'Data Scientist',
    skills: ['python', 'machine learning'],
    resumeText: `Rahul Verma - Data Scientist
Master's degree in Data Science.
5 years of experience in machine learning and data analysis.
Skills: Python, pandas, NumPy, scikit-learn, TensorFlow, SQL, PostgreSQL, Tableau, NLP, deep learning.
Built a customer churn prediction model and an NLP pipeline for resume classification.`,
  },
  {
    key: 'sneha',
    name: 'Sneha Reddy',
    title: 'Frontend Developer (Fresher)',
    skills: ['html', 'css', 'javascript'],
    resumeText: `Sneha Reddy - Frontend Developer
Bachelor of Technology in Information Technology, 2026.
Skills: HTML, CSS, JavaScript, React, Tailwind, Figma, Git.
Internship: built responsive landing pages and a React dashboard. 1 year of experience including internships.`,
  },
  {
    key: 'karthik',
    name: 'Karthik Nair',
    title: 'DevOps Engineer',
    skills: ['aws', 'docker', 'kubernetes'],
    resumeText: `Karthik Nair - DevOps / Cloud Engineer
Bachelor's degree in Electronics and Communication.
6 years of experience in cloud infrastructure.
Skills: AWS, Docker, Kubernetes, Terraform, Jenkins, CI/CD, Linux, Python, Bash, Prometheus.
Migrated monolith services to Kubernetes on AWS EKS, cutting deploy time by 70%.`,
  },
];

const jobs = [
  {
    employer: 'techcorp',
    title: 'MERN Stack Developer',
    location: 'Chennai',
    jobType: 'full-time',
    experienceLevel: 'mid',
    salaryMin: 800000,
    salaryMax: 1400000,
    skillsRequired: ['react', 'node.js', 'express', 'mongodb', 'javascript'],
    description:
      'Build and maintain full-stack web applications using React on the frontend and Node.js/Express with MongoDB on the backend. Design REST APIs and work in an agile team.',
  },
  {
    employer: 'techcorp',
    title: 'Frontend Developer Intern',
    location: 'Bengaluru',
    jobType: 'internship',
    experienceLevel: 'entry',
    salaryMin: 20000,
    salaryMax: 30000,
    skillsRequired: ['html', 'css', 'javascript', 'react'],
    description:
      'Work with our design team to build responsive, accessible user interfaces in React. Great opportunity for final-year students and fresh graduates.',
  },
  {
    employer: 'techcorp',
    title: 'Senior DevOps Engineer',
    location: 'Remote',
    jobType: 'full-time',
    experienceLevel: 'senior',
    salaryMin: 2000000,
    salaryMax: 3000000,
    skillsRequired: ['aws', 'docker', 'kubernetes', 'terraform', 'jenkins'],
    description:
      'Own our cloud infrastructure on AWS. Build CI/CD pipelines, manage Kubernetes clusters and drive infrastructure-as-code with Terraform.',
  },
  {
    employer: 'datawise',
    title: 'Machine Learning Engineer',
    location: 'Hyderabad',
    jobType: 'full-time',
    experienceLevel: 'mid',
    salaryMin: 1200000,
    salaryMax: 2000000,
    skillsRequired: ['python', 'machine learning', 'tensorflow', 'pandas', 'sql'],
    description:
      'Design, train and deploy machine learning models for analytics products. Work with large datasets using Python, pandas and SQL.',
  },
  {
    employer: 'datawise',
    title: 'Data Analyst',
    location: 'Pune',
    jobType: 'full-time',
    experienceLevel: 'entry',
    salaryMin: 500000,
    salaryMax: 800000,
    skillsRequired: ['sql', 'python', 'tableau', 'excel'],
    description:
      'Analyze business data, build dashboards in Tableau and present insights to stakeholders. SQL and Python required.',
  },
];

// [candidate, job title, status]
const applications = [
  ['ananya', 'MERN Stack Developer', 'shortlisted'],
  ['sneha', 'MERN Stack Developer', 'applied'],
  ['sneha', 'Frontend Developer Intern', 'applied'],
  ['ananya', 'Frontend Developer Intern', 'applied'],
  ['rahul', 'Machine Learning Engineer', 'hired'],
  ['rahul', 'Data Analyst', 'applied'],
  ['karthik', 'Senior DevOps Engineer', 'shortlisted'],
];

const email = (key) => `${key}${DOMAIN}`;

async function clearDemoData() {
  const demoUsers = await User.find({ email: { $regex: `${DOMAIN.replace('.', '\\.')}$` } });
  const ids = demoUsers.map((u) => u._id);
  const demoJobs = await Job.find({ employer: { $in: ids } }).select('_id');
  await Application.deleteMany({
    $or: [{ candidate: { $in: ids } }, { job: { $in: demoJobs.map((j) => j._id) } }],
  });
  await Job.deleteMany({ employer: { $in: ids } });
  await User.deleteMany({ _id: { $in: ids } });
}

async function seedDemo() {
  await connectDB();
  await clearDemoData();

  await User.create({ name: 'Demo Admin', email: email('admin'), password: PASSWORD, role: 'admin' });

  const employerDocs = {};
  for (const e of employers) {
    employerDocs[e.key] = await User.create({
      name: e.name,
      email: email(e.key),
      password: PASSWORD,
      role: 'employer',
      company: e.company,
      title: e.title,
    });
  }

  const candidateDocs = {};
  for (const c of candidates) {
    candidateDocs[c.key] = await User.create({
      name: c.name,
      email: email(c.key),
      password: PASSWORD,
      role: 'candidate',
      title: c.title,
      skills: c.skills,
      resumeText: c.resumeText,
    });
  }

  const jobDocs = {};
  for (const j of jobs) {
    const employer = employerDocs[j.employer];
    jobDocs[j.title] = await Job.create({ ...j, company: employer.company, employer: employer._id });
  }

  for (const [candidateKey, jobTitle, status] of applications) {
    const candidate = candidateDocs[candidateKey];
    const job = jobDocs[jobTitle];
    const result = computeMatchScore(candidate.resumeText, job, candidate.skills);
    await Application.create({
      job: job._id,
      candidate: candidate._id,
      resumePath: 'demo-seed',
      resumeOriginalName: `${candidate.name.replace(/\s+/g, '_')}_Resume.txt`,
      resumeText: candidate.resumeText,
      extractedSkills: result.extractedSkills,
      matchScore: result.score,
      status,
      matchDetails: {
        skillMatchPercent: result.skillMatchPercent,
        textSimilarityPercent: result.textSimilarityPercent,
        experienceFitPercent: result.experienceFitPercent,
        candidateYearsOfExperience: result.candidateYearsOfExperience,
        educationLevel: result.educationLevel,
        matchedSkills: result.matchedSkills,
        missingSkills: result.missingSkills,
      },
    });
    job.applicationsCount += 1;
    await job.save();
    console.log(`  ${candidate.name} -> ${jobTitle}: ${result.score}% match (${status})`);
  }

  console.log('\nDemo data created. All accounts use password:', PASSWORD);
  console.log(`  Admin:      ${email('admin')}`);
  employers.forEach((e) => console.log(`  Employer:   ${email(e.key)}  (${e.company})`));
  candidates.forEach((c) => console.log(`  Candidate:  ${email(c.key)}  (${c.title})`));

  await mongoose.disconnect();
}

seedDemo().catch(async (err) => {
  console.error(err);
  await mongoose.disconnect();
  process.exit(1);
});
