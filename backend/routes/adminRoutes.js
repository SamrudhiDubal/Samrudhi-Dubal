const express = require('express');
const {
  getStats,
  getUsers,
  updateUser,
  deleteUser,
  getAllJobs,
  moderateJob,
  deleteAnyJob,
  getAllApplications,
} = require('../controllers/adminController');
const { protect, authorize } = require('../middleware/auth');

const router = express.Router();

router.use(protect, authorize('admin'));

router.get('/stats', getStats);

router.get('/users', getUsers);
router.put('/users/:id', updateUser);
router.delete('/users/:id', deleteUser);

router.get('/jobs', getAllJobs);
router.put('/jobs/:id', moderateJob);
router.delete('/jobs/:id', deleteAnyJob);

router.get('/applications', getAllApplications);

module.exports = router;
