const express = require('express');
const {
  createJob,
  getJobs,
  getJobById,
  getMyJobs,
  updateJob,
  deleteJob,
} = require('../controllers/jobController');
const { protect, authorize } = require('../middleware/auth');

const router = express.Router();

router.get('/', getJobs);
router.get('/employer/mine', protect, authorize('employer'), getMyJobs);
router.get('/:id', getJobById);
router.post('/', protect, authorize('employer'), createJob);
router.put('/:id', protect, authorize('employer'), updateJob);
router.delete('/:id', protect, authorize('employer'), deleteJob);

module.exports = router;
