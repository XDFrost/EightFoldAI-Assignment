const express = require('express');
const cors = require('cors');
require('dotenv').config();

const authRoutes = require('./routes/authRoutes');
const analyticsRoutes = require('./routes/analyticsRoutes');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use('/auth', authRoutes);
app.use('/analytics', analyticsRoutes);
app.use('/conversations', require('./routes/conversationRoutes'));

// Health Check
app.get('/', (req, res) => {
    res.send('Business Backend is running');
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
