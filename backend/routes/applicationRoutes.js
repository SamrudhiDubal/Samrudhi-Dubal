const express = require('express');
const {
  applyToJob,
  getMyApplications,
  getApplicantsForJob,
  getApplicationById,
  updateApplicationStatus,
} = require('../controllers/applicationController');
const { protect, authorize } = require('../middleware/auth');
const upload = require('../middleware/upload');

const router = express.Router();

router.get('/mine', protect, authorize('candidate'), getMyApplications);
router.get('/job/:jobId', protect, authorize('employer'), getApplicantsForJob);
router.get('/:id', protect, getApplicationById);
router.post(
  '/:jobId',
  protect,
  authorize('candidate'),
  upload.single('resume'),
  applyToJob
);
router.put('/:id/status', protect, authorize('employer'), updateApplicationStatus);

module.exports = router;
