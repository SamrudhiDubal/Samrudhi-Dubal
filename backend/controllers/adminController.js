const User = require('../models/User');
const Job = require('../models/Job');
const Application = require('../models/Application');

// @desc    Platform-wide stats for the admin dashboard
// @route   GET /api/admin/stats
const getStats = async (req, res, next) => {
  try {
    const [
      totalUsers,
      candidateCount,
      employerCount,
      totalJobs,
      openJobs,
      totalApplications,
      applicationsByStatus,
      avgMatchScoreAgg,
    ] = await Promise.all([
      User.countDocuments({ role: { $ne: 'admin' } }),
      User.countDocuments({ role: 'candidate' }),
      User.countDocuments({ role: 'employer' }),
      Job.countDocuments(),
      Job.countDocuments({ status: 'open' }),
      Application.countDocuments(),
      Application.aggregate([{ $group: { _id: '$status', count: { $sum: 1 } } }]),
      Application.aggregate([{ $group: { _id: null, avg: { $avg: '$matchScore' } } }]),
    ]);

    const statusCounts = applicationsByStatus.reduce((acc, row) => {
      acc[row._id] = row.count;
      return acc;
    }, {});

    res.json({
      users: { total: totalUsers, candidates: candidateCount, employers: employerCount },
      jobs: { total: totalJobs, open: openJobs, closed: totalJobs - openJobs },
      applications: {
        total: totalApplications,
        byStatus: statusCounts,
        averageMatchScore: Math.round(avgMatchScoreAgg[0]?.avg || 0),
      },
    });
  } catch (err) {
    next(err);
  }
};

// @desc    List all users (any role), with optional role filter and search
// @route   GET /api/admin/users
const getUsers = async (req, res, next) => {
  try {
    const { role, search, page = 1, limit = 20 } = req.query;
    const query = {};
    if (role) query.role = role;
    if (search) {
      query.$or = [
        { name: { $regex: search, $options: 'i' } },
        { email: { $regex: search, $options: 'i' } },
      ];
    }

    const pageNum = Math.max(1, parseInt(page, 10) || 1);
    const limitNum = Math.min(100, Math.max(1, parseInt(limit, 10) || 20));

    const [users, total] = await Promise.all([
      User.find(query)
        .sort({ createdAt: -1 })
        .skip((pageNum - 1) * limitNum)
        .limit(limitNum),
      User.countDocuments(query),
    ]);

    res.json({ users, total, page: pageNum, pages: Math.ceil(total / limitNum) });
  } catch (err) {
    next(err);
  }
};

// @desc    Activate/deactivate a user or change their role
// @route   PUT /api/admin/users/:id
const updateUser = async (req, res, next) => {
  try {
    const { isActive, role } = req.body;
    if (req.params.id === req.user._id.toString()) {
      return res.status(400).json({ message: 'Admins cannot modify their own account here' });
    }

    const updates = {};
    if (isActive !== undefined) updates.isActive = isActive;
    if (role !== undefined) {
      if (!['candidate', 'employer', 'admin'].includes(role)) {
        return res.status(400).json({ message: 'Invalid role' });
      }
      updates.role = role;
    }

    const user = await User.findByIdAndUpdate(req.params.id, updates, {
      new: true,
      runValidators: true,
    });
    if (!user) return res.status(404).json({ message: 'User not found' });
    res.json({ user: user.toSafeObject() });
  } catch (err) {
    next(err);
  }
};

// @desc    Delete a user and cascade their jobs/applications
// @route   DELETE /api/admin/users/:id
const deleteUser = async (req, res, next) => {
  try {
    if (req.params.id === req.user._id.toString()) {
      return res.status(400).json({ message: 'Admins cannot delete their own account here' });
    }
    const user = await User.findById(req.params.id);
    if (!user) return res.status(404).json({ message: 'User not found' });

    if (user.role === 'employer') {
      const jobs = await Job.find({ employer: user._id }, '_id');
      await Application.deleteMany({ job: { $in: jobs.map((j) => j._id) } });
      await Job.deleteMany({ employer: user._id });
    } else if (user.role === 'candidate') {
      await Application.deleteMany({ candidate: user._id });
    }
    await user.deleteOne();
    res.json({ message: 'User and associated data deleted' });
  } catch (err) {
    next(err);
  }
};

// @desc    List all jobs platform-wide (any status)
// @route   GET /api/admin/jobs
const getAllJobs = async (req, res, next) => {
  try {
    const { status, page = 1, limit = 20 } = req.query;
    const query = {};
    if (status) query.status = status;

    const pageNum = Math.max(1, parseInt(page, 10) || 1);
    const limitNum = Math.min(100, Math.max(1, parseInt(limit, 10) || 20));

    const [jobs, total] = await Promise.all([
      Job.find(query)
        .populate('employer', 'name email company')
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

// @desc    Force-close or reopen any job
// @route   PUT /api/admin/jobs/:id
const moderateJob = async (req, res, next) => {
  try {
    const { status } = req.body;
    if (!['open', 'closed'].includes(status)) {
      return res.status(400).json({ message: 'Status must be open or closed' });
    }
    const job = await Job.findByIdAndUpdate(req.params.id, { status }, { new: true });
    if (!job) return res.status(404).json({ message: 'Job not found' });
    res.json({ job });
  } catch (err) {
    next(err);
  }
};

// @desc    Delete any job (admin override)
// @route   DELETE /api/admin/jobs/:id
const deleteAnyJob = async (req, res, next) => {
  try {
    const job = await Job.findById(req.params.id);
    if (!job) return res.status(404).json({ message: 'Job not found' });
    await Application.deleteMany({ job: job._id });
    await job.deleteOne();
    res.json({ message: 'Job deleted' });
  } catch (err) {
    next(err);
  }
};

// @desc    List all applications platform-wide
// @route   GET /api/admin/applications
const getAllApplications = async (req, res, next) => {
  try {
    const { status, page = 1, limit = 20 } = req.query;
    const query = {};
    if (status) query.status = status;

    const pageNum = Math.max(1, parseInt(page, 10) || 1);
    const limitNum = Math.min(100, Math.max(1, parseInt(limit, 10) || 20));

    const [applications, total] = await Promise.all([
      Application.find(query)
        .populate('job', 'title company')
        .populate('candidate', 'name email')
        .sort({ createdAt: -1 })
        .skip((pageNum - 1) * limitNum)
        .limit(limitNum),
      Application.countDocuments(query),
    ]);

    res.json({ applications, total, page: pageNum, pages: Math.ceil(total / limitNum) });
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getStats,
  getUsers,
  updateUser,
  deleteUser,
  getAllJobs,
  moderateJob,
  deleteAnyJob,
  getAllApplications,
};
