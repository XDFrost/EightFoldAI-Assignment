const express = require('express');
const cors = require('cors');
require('dotenv').config();

const authRoutes = require('./routes/authRoutes');
const analyticsRoutes = require('./routes/analyticsRoutes');

const app = express();
const PORT = process.env.PORT || 3000;

const rawOrigins = process.env.ALLOWED_ORIGINS?.split(",") || [];
const allowAll = rawOrigins.includes("*");

app.use(cors({
    origin: (origin, callback) => {
        if (allowAll) {
            return callback(null, true);
        }
        if (!origin || rawOrigins.includes(origin)) {
            return callback(null, true);
        }
        return callback(new Error("Not allowed by CORS"));
    },
    credentials: true,
}));


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
