const express = require('express');
const {
  createJob,
  getJobs,
  getJobById,
  getMyJobs,
  updateJob,
  deleteJob,
  getRecommendedJobs,
  getMatchingCandidates,
} = require('../controllers/jobController');
const { protect, authorize } = require('../middleware/auth');

const router = express.Router();

router.get('/', getJobs);
router.get('/employer/mine', protect, authorize('employer'), getMyJobs);
router.get('/recommended', protect, authorize('candidate'), getRecommendedJobs);
router.get('/:id/matching-candidates', protect, authorize('employer'), getMatchingCandidates);
router.get('/:id', getJobById);
router.post('/', protect, authorize('employer'), createJob);
router.put('/:id', protect, authorize('employer'), updateJob);
router.delete('/:id', protect, authorize('employer'), deleteJob);

module.exports = router;
