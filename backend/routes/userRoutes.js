const express = require('express');
const { updateMe, uploadProfileResume } = require('../controllers/userController');
const { protect, authorize } = require('../middleware/auth');
const upload = require('../middleware/upload');

const router = express.Router();

router.put('/me', protect, updateMe);
router.post(
  '/me/resume',
  protect,
  authorize('candidate'),
  upload.single('resume'),
  uploadProfileResume
);

module.exports = router;
