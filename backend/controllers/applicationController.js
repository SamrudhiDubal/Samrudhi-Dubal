const fs = require('fs');
const path = require('path');
const Application = require('../models/Application');
const Job = require('../models/Job');
const { extractResumeText } = require('../utils/resumeParser');
const { computeMatchScore } = require('../utils/aiMatcher');

// @desc    Apply to a job with a resume upload; AI engine scores the match
// @route   POST /api/applications/:jobId
const applyToJob = async (req, res, next) => {
  try {
    const job = await Job.findById(req.params.jobId);
    if (!job) {
      if (req.file) fs.unlink(req.file.path, () => {});
      return res.status(404).json({ message: 'Job not found' });
    }
    if (job.status !== 'open') {
      if (req.file) fs.unlink(req.file.path, () => {});
      return res.status(400).json({ message: 'This job is no longer accepting applications' });
    }
    if (!req.file) {
      return res.status(400).json({ message: 'A resume file is required' });
    }

    const existing = await Application.findOne({ job: job._id, candidate: req.user._id });
    if (existing) {
      fs.unlink(req.file.path, () => {});
      return res.status(409).json({ message: 'You have already applied to this job' });
    }

    let resumeText = '';
    try {
      resumeText = await extractResumeText(req.file.path);
    } catch (parseErr) {
      fs.unlink(req.file.path, () => {});
      return res.status(422).json({
        message: `Could not parse resume: ${parseErr.message}`,
      });
    }

    const matchResult = computeMatchScore(resumeText, job, req.user.skills);

    const application = await Application.create({
      job: job._id,
      candidate: req.user._id,
      resumePath: path.relative(path.join(__dirname, '..'), req.file.path),
      resumeOriginalName: req.file.originalname,
      resumeText,
      coverLetter: req.body.coverLetter,
      extractedSkills: matchResult.extractedSkills,
      matchScore: matchResult.score,
      matchDetails: {
        skillMatchPercent: matchResult.skillMatchPercent,
        textSimilarityPercent: matchResult.textSimilarityPercent,
        matchedSkills: matchResult.matchedSkills,
        missingSkills: matchResult.missingSkills,
      },
    });

    job.applicationsCount = (job.applicationsCount || 0) + 1;
    await job.save();

    res.status(201).json({ application });
  } catch (err) {
    if (req.file) fs.unlink(req.file.path, () => {});
    next(err);
  }
};

// @desc    Applications submitted by the logged in candidate
// @route   GET /api/applications/mine
const getMyApplications = async (req, res, next) => {
  try {
    const applications = await Application.find({ candidate: req.user._id })
      .populate('job', 'title company location status jobType')
      .sort({ createdAt: -1 });
    res.json({ applications });
  } catch (err) {
    next(err);
  }
};

// @desc    Ranked applicants for a job, sorted by AI match score (employer, owner only)
// @route   GET /api/applications/job/:jobId
const getApplicantsForJob = async (req, res, next) => {
  try {
    const job = await Job.findById(req.params.jobId);
    if (!job) return res.status(404).json({ message: 'Job not found' });
    if (job.employer.toString() !== req.user._id.toString()) {
      return res.status(403).json({ message: 'You do not own this job posting' });
    }

    const applications = await Application.find({ job: job._id })
      .populate('candidate', 'name email title skills resumePath')
      .sort({ matchScore: -1, createdAt: -1 });

    res.json({ job: { _id: job._id, title: job.title }, applications });
  } catch (err) {
    next(err);
  }
};

// @desc    Get a single application (owner candidate or owner employer)
// @route   GET /api/applications/:id
const getApplicationById = async (req, res, next) => {
  try {
    const application = await Application.findById(req.params.id)
      .populate('job')
      .populate('candidate', 'name email title skills');
    if (!application) return res.status(404).json({ message: 'Application not found' });

    const isCandidateOwner = application.candidate._id.toString() === req.user._id.toString();
    const isEmployerOwner = application.job.employer.toString() === req.user._id.toString();
    if (!isCandidateOwner && !isEmployerOwner && req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Not authorized to view this application' });
    }

    res.json({ application });
  } catch (err) {
    next(err);
  }
};

// @desc    Update application status (employer, owner only)
// @route   PUT /api/applications/:id/status
const updateApplicationStatus = async (req, res, next) => {
  try {
    const { status } = req.body;
    const allowed = ['applied', 'shortlisted', 'rejected', 'hired'];
    if (!allowed.includes(status)) {
      return res.status(400).json({ message: `Status must be one of: ${allowed.join(', ')}` });
    }

    const application = await Application.findById(req.params.id).populate('job');
    if (!application) return res.status(404).json({ message: 'Application not found' });
    if (application.job.employer.toString() !== req.user._id.toString()) {
      return res.status(403).json({ message: 'You do not own this job posting' });
    }

    application.status = status;
    await application.save();
    res.json({ application });
  } catch (err) {
    next(err);
  }
};

module.exports = {
  applyToJob,
  getMyApplications,
  getApplicantsForJob,
  getApplicationById,
  updateApplicationStatus,
};
