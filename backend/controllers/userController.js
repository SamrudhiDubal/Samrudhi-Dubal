const fs = require('fs');
const User = require('../models/User');
const { extractResumeText } = require('../utils/resumeParser');
const { extractSkills } = require('../utils/skillsDictionary');

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

// @desc    Upload a resume to the candidate's profile; its text powers job
//          recommendations and employer-side candidate matching
// @route   POST /api/users/me/resume
const uploadProfileResume = async (req, res, next) => {
  if (!req.file) return res.status(400).json({ message: 'A resume file is required' });
  try {
    let resumeText;
    try {
      resumeText = await extractResumeText(req.file.path);
    } catch (parseErr) {
      return res.status(422).json({ message: `Could not parse resume: ${parseErr.message}` });
    } finally {
      // Only the extracted text is kept on the profile, not the file itself.
      fs.unlink(req.file.path, () => {});
    }

    req.user.resumeText = resumeText;
    await req.user.save();
    res.json({ user: req.user.toSafeObject(), detectedSkills: extractSkills(resumeText) });
  } catch (err) {
    next(err);
  }
};

module.exports = { updateMe, uploadProfileResume };
