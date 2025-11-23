const express = require('express');
const router = express.Router();
const analyticsController = require('../controllers/analyticsController');
const { authenticateToken, authorizeRole } = require('../middleware/authMiddleware');

router.get('/usage', authenticateToken, authorizeRole('admin'), analyticsController.getUsageStats);

module.exports = router;
