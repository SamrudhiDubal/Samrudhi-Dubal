const express = require('express');
const { updateMe } = require('../controllers/userController');
const { protect } = require('../middleware/auth');

const router = express.Router();

router.put('/me', protect, updateMe);

module.exports = router;
