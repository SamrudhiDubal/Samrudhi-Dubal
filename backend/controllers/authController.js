const User = require('../models/User');
const generateToken = require('../utils/generateToken');

// @desc    Register a new user (candidate or employer)
// @route   POST /api/auth/register
const register = async (req, res, next) => {
  try {
    const { name, email, password, role, company, title, skills } = req.body;

    if (!name || !email || !password) {
      return res.status(400).json({ message: 'Name, email and password are required' });
    }

    const existing = await User.findOne({ email: email.toLowerCase() });
    if (existing) {
      return res.status(409).json({ message: 'An account with this email already exists' });
    }

    if (role === 'admin') {
      return res.status(403).json({ message: 'Cannot self-register as admin' });
    }

    const user = await User.create({
      name,
      email,
      password,
      role: role === 'employer' ? 'employer' : 'candidate',
      company,
      title,
      skills: Array.isArray(skills) ? skills : [],
    });

    const token = generateToken(user._id);
    res.status(201).json({ token, user: user.toSafeObject() });
  } catch (err) {
    next(err);
  }
};

// @desc    Login
// @route   POST /api/auth/login
const login = async (req, res, next) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required' });
    }

    const user = await User.findOne({ email: email.toLowerCase() }).select('+password');
    if (!user || !(await user.comparePassword(password))) {
      return res.status(401).json({ message: 'Invalid email or password' });
    }

    const token = generateToken(user._id);
    res.json({ token, user: user.toSafeObject() });
  } catch (err) {
    next(err);
  }
};

// @desc    Get current logged in user
// @route   GET /api/auth/me
const getMe = async (req, res) => {
  res.json({ user: req.user.toSafeObject() });
};

module.exports = { register, login, getMe };
