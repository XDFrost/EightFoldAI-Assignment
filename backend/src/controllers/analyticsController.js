const db = require('../config/db');

exports.getUsageStats = async (req, res) => {
    try {
        const totalUsers = await db.query('SELECT COUNT(*) FROM users');
        const totalPlans = await db.query('SELECT COUNT(*) FROM account_plans');
        const totalResearch = await db.query('SELECT COUNT(*) FROM research_data');

        // Get recent plans with user info
        const recentPlans = await db.query(`
      SELECT ap.id, ap.company, ap.created_at, u.email 
      FROM account_plans ap 
      JOIN users u ON ap.user_id = u.id 
      ORDER BY ap.created_at DESC 
      LIMIT 10
    `);

        res.json({
            counts: {
                users: parseInt(totalUsers.rows[0].count),
                plans: parseInt(totalPlans.rows[0].count),
                research: parseInt(totalResearch.rows[0].count)
            },
            recentActivity: recentPlans.rows
        });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
    }
};
