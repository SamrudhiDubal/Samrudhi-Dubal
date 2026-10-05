const Job = require('../models/Job');
const Application = require('../models/Application');
const User = require('../models/User');
const { recommendJobsForCandidate, matchCandidatesForJob } = require('../utils/recommender');

// @desc    Create a job posting
// @route   POST /api/jobs
const createJob = async (req, res, next) => {
  try {
    const {
      title,
      description,
      company,
      location,
      jobType,
      experienceLevel,
      salaryMin,
      salaryMax,
      skillsRequired,
    } = req.body;

    if (!title || !description || !company) {
      return res.status(400).json({ message: 'Title, description and company are required' });
    }

    const job = await Job.create({
      title,
      description,
      company,
      location,
      jobType,
      experienceLevel,
      salaryMin,
      salaryMax,
      skillsRequired: Array.isArray(skillsRequired)
        ? skillsRequired.map((s) => s.toLowerCase().trim())
        : [],
      employer: req.user._id,
    });

    res.status(201).json({ job });
  } catch (err) {
    next(err);
  }
};

// @desc    List / search jobs (public)
// @route   GET /api/jobs
const getJobs = async (req, res, next) => {
  try {
    const { search, location, jobType, experienceLevel, skill, page = 1, limit = 10 } = req.query;
    const query = { status: 'open' };

    if (search) {
      query.$text = { $search: search };
    }
    if (location) {
      query.location = { $regex: location, $options: 'i' };
    }
    if (jobType) {
      query.jobType = jobType;
    }
    if (experienceLevel) {
      query.experienceLevel = experienceLevel;
    }
    if (skill) {
      query.skillsRequired = skill.toLowerCase();
    }

    const pageNum = Math.max(1, parseInt(page, 10) || 1);
    const limitNum = Math.min(50, Math.max(1, parseInt(limit, 10) || 10));

    const [jobs, total] = await Promise.all([
      Job.find(query)
        .populate('employer', 'name company')
        .sort({ createdAt: -1 })
        .skip((pageNum - 1) * limitNum)
        .limit(limitNum),
      Job.countDocuments(query),
    ]);

    res.json({ jobs, total, page: pageNum, pages: Math.ceil(total / limitNum) });
  } catch (err) {
    next(err);
  }
};

// @desc    Get single job
// @route   GET /api/jobs/:id
const getJobById = async (req, res, next) => {
  try {
    const job = await Job.findById(req.params.id).populate('employer', 'name company');
    if (!job) return res.status(404).json({ message: 'Job not found' });
    res.json({ job });
  } catch (err) {
    next(err);
  }
};

// @desc    Jobs posted by the logged in employer
// @route   GET /api/jobs/employer/mine
const getMyJobs = async (req, res, next) => {
  try {
    const jobs = await Job.find({ employer: req.user._id }).sort({ createdAt: -1 });
    res.json({ jobs });
  } catch (err) {
    next(err);
  }
};

// @desc    Update a job (owner only)
// @route   PUT /api/jobs/:id
const updateJob = async (req, res, next) => {
  try {
    const job = await Job.findById(req.params.id);
    if (!job) return res.status(404).json({ message: 'Job not found' });
    if (job.employer.toString() !== req.user._id.toString()) {
      return res.status(403).json({ message: 'You do not own this job posting' });
    }

    const allowedFields = [
      'title',
      'description',
      'company',
      'location',
      'jobType',
      'experienceLevel',
      'salaryMin',
      'salaryMax',
      'skillsRequired',
      'status',
    ];
    for (const field of allowedFields) {
      if (req.body[field] !== undefined) {
        job[field] =
          field === 'skillsRequired'
            ? req.body[field].map((s) => s.toLowerCase().trim())
            : req.body[field];
      }
    }
    await job.save();
    res.json({ job });
  } catch (err) {
    next(err);
  }
};

// @desc    Delete a job (owner only)
// @route   DELETE /api/jobs/:id
const deleteJob = async (req, res, next) => {
  try {
    const job = await Job.findById(req.params.id);
    if (!job) return res.status(404).json({ message: 'Job not found' });
    if (job.employer.toString() !== req.user._id.toString()) {
      return res.status(403).json({ message: 'You do not own this job posting' });
    }
    await Application.deleteMany({ job: job._id });
    await job.deleteOne();
    res.json({ message: 'Job deleted' });
  } catch (err) {
    next(err);
  }
};

// @desc    Open jobs ranked by AI match against the candidate's profile/resume
// @route   GET /api/jobs/recommended
const getRecommendedJobs = async (req, res, next) => {
  try {
    const limit = Math.min(50, Math.max(1, parseInt(req.query.limit, 10) || 10));
    const [jobs, applied] = await Promise.all([
      Job.find({ status: 'open' }).populate('employer', 'name company'),
      Application.find({ candidate: req.user._id }).distinct('job'),
    ]);
    const appliedIds = new Set(applied.map((id) => id.toString()));

    const recommendations = recommendJobsForCandidate(req.user, jobs, { limit }).map(
      ({ job, match }) => ({ job, match, alreadyApplied: appliedIds.has(job._id.toString()) })
    );

    res.json({
      basedOn: req.user.resumeText ? 'resume' : 'profile',
      recommendations,
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Candidates on the platform ranked by AI match for a job (owner only),
//          including candidates who have not applied yet
// @route   GET /api/jobs/:id/matching-candidates
const getMatchingCandidates = async (req, res, next) => {
  try {
    const job = await Job.findById(req.params.id);
    if (!job) return res.status(404).json({ message: 'Job not found' });
    if (job.employer.toString() !== req.user._id.toString()) {
      return res.status(403).json({ message: 'You do not own this job posting' });
    }

    const limit = Math.min(50, Math.max(1, parseInt(req.query.limit, 10) || 20));
    const minScore = Math.max(0, parseInt(req.query.minScore, 10) || 0);

    const [candidates, applicants] = await Promise.all([
      User.find({ role: 'candidate', isActive: true }).select(
        'name email title bio skills resumeText'
      ),
      Application.find({ job: job._id }).distinct('candidate'),
    ]);
    const applicantIds = new Set(applicants.map((id) => id.toString()));

    const matches = matchCandidatesForJob(job, candidates, { limit, minScore }).map(
      ({ candidate, match }) => ({
        candidate: {
          _id: candidate._id,
          name: candidate.name,
          email: candidate.email,
          title: candidate.title,
          skills: candidate.skills,
          hasResume: Boolean(candidate.resumeText),
        },
        match,
        hasApplied: applicantIds.has(candidate._id.toString()),
      })
    );

    res.json({ job: { _id: job._id, title: job.title }, matches });
  } catch (err) {
    next(err);
  }
};

module.exports = {
  createJob,
  getJobs,
  getJobById,
  getMyJobs,
  updateJob,
  deleteJob,
  getRecommendedJobs,
  getMatchingCandidates,
};
