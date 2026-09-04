const User = require('../models/User');

// @desc    Update own profile (candidate skills/bio, employer company)
// @route   PUT /api/users/me
const updateMe = async (req, res, next) => {
  try {
    const allowedFields = ['name', 'title', 'bio', 'skills', 'company'];
    const updates = {};
    for (const field of allowedFields) {
      if (req.body[field] !== undefined) updates[field] = req.body[field];
    }
    const user = await User.findByIdAndUpdate(req.user._id, updates, {
      new: true,
      runValidators: true,
    });
    res.json({ user: user.toSafeObject() });
  } catch (err) {
    next(err);
  }
};

module.exports = { updateMe };
