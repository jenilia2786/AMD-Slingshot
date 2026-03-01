const express = require('express');
const dotenv = require('dotenv');
const connectDB = require('./config/db');

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();

// Body parser
app.use(express.json());

/**
 * Connect to Database
 * We ensure DB connects before the server starts by calling it here
 */
const startServer = async () => {
    await connectDB();

    // Define existing routes (Example placeholders)
    app.get('/', (req, res) => {
        res.json({ message: 'Antigravity Backend API is running' });
    });

    // Example route
    app.get('/api/status', (req, res) => {
        res.json({ status: 'Connected to MongoDB', database: 'antigravity' });
    });

    const PORT = process.env.PORT || 5000;

    app.listen(PORT, () => {
        console.log(`🚀 Server running in ${process.env.NODE_ENV || 'development'} mode on port ${PORT}`);
    });
};

// Start the server
startServer();
