//We may need to update this. I dont know if we should be requiring API key to see web pages. Also we need 

const express = require("express");
const { authenticateToken, authenticateApiKey } = require("../middlewares/auth-middleware");
const path = require('path');
const db = require("../utils/db");
const jwt = require('jsonwebtoken');
const bcryptjs = require('bcryptjs')

const router = express.Router();

router.use(express.static(path.join(__dirname, '../../../../Frontend')));

router.get('/form', (req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend', 'survey.html'));
});

router.get('/login', (req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend', 'login.html'));
});

router.get('/leader-response', (req, res) => {
    res.sendFile(path.join(__dirname, '../../../Frontend', 'leader_response.html'));
});

router.get('/engagement-metrics', (req, res) => {
    res.sendFile(path.join(__dirname, '../../../Frontend', 'engagement_metrics.html'));
});


router.post('/login', async (req, res) => {
    const { username, password } = req.body;

    try {
        // Get the user from the database
        const [rows] = await db.execute("SELECT * FROM users WHERE UserUN = ?", [username]);

        if (rows.length === 0) {
            return res.status(400).json({ message: "Invalid credentials" });
        }

        const user = rows[0];

        // Compare the provided password with the hashed password in the database
        const isPasswordValid = await bcryptjs.compare(password, user.UserPW);

        if (!isPasswordValid) {
            return res.status(400).json({ message: "Invalid credentials" });
        }

        // Generate JWT token
        const token = jwt.sign(
            { id: user.UserID, UserUN: user.UserUN, isAdmin: user.isAdmin },
            process.env.JWT_SECRET,  // Secret key for signing the JWT
            { expiresIn: "1h" }  // Token expires in 1 hour
        );

        res.json({ message: "Login successful", token });

    } catch (error) {
        console.error("Login error:", error);
        res.status(500).json({ message: "Internal server error" });
    }
});

// Using the authenticateToken middleware to automatically handle token validation -> checking if user is an admin
router.get('/check-admin', authenticateToken, async (req, res) => {
    res.json({ isAdmin: req.user.isAdmin });
});


router.get('/dashboard', authenticateApiKey, (req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend', 'dashboard.html'));

});

router.get('/main', authenticateApiKey, (req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend/response_board', 'main.html'));

});

router.get('/board', authenticateApiKey, (req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend', 'board.html'));

});

// POST - Submit feedback
router.post("/feedback", authenticateApiKey, async (req, res) => {
    const { feedback, comment1, comment2, comment3 } = req.body;

    if (!feedback || !["thumbs_up", "thumbs_down", "thumbs_middle"].includes(feedback)) {
        return res.status(400).json({ message: "Invalid feedback value." });
    }

    try {
        const sql = "INSERT INTO feedback (feedback, comment1, comment2, comment3) VALUES (?, ?, ?, ?)";
        const [result] = await db.execute(sql, [feedback, comment1, comment2, comment3]);
        res.status(201).json({ message: "Feedback submitted successfully.", id: result.insertId });
    } catch (error) {
        console.error("Database error:", error);
        res.status(500).json({ message: "Internal server error." });
    }
});

const { respondToFeedback } = require('../models/feedback-model');

router.post("/response", authenticateToken, async (req, res) => {
    const { responseId, leaderResponse } = req.body;
    if (!responseId || !leaderResponse) {
        return res.status(400).json({ message: "Response ID and leader response are required." });
    }
    try {
        await respondToFeedback(req, res);
    } catch (error) {
        console.error("Database error:", error);
        res.status(500).json({ message: "Internal server error." });
    }
});




// GET - Fetch feedback (Protected)
// Do we need to auth the token here? Commented it out for now

// authenticateToken was supposed to require admin privileges bc then anyone with an account
// could navigate to the route manually with the URL and view all the feedback as a json file...

router.get("/feedback", authenticateApiKey,
    authenticateToken, 
    async (req, res) => {

        try {
            const [rows] = await db.execute("SELECT * FROM feedback");
            res.json(rows);
        } catch (error) {
            console.error("Database error:", error);
            res.status(500).json({ message: "Internal server error." });
        }
    });

router.get("/response", authenticateApiKey,
    authenticateToken, 
    async (req, res) => {
        try {
            const [rows] = await db.execute("SELECT * FROM responses");
            //TODO: Add where clause. Leave now for testing.
            res.json(rows);
        } catch (error) {
            console.error("Database error:", error);
            res.status(500).json({ message: "Internal server error." });
        }
    });

// GET - Engagement metrics
router.get("/metrics", authenticateToken, async (req, res) => {
    try {
        const { start, end } = req.query;

        let query = "SELECT survey_category, COUNT(*) AS count FROM feedback";
        let params = [];

        if (start && end) {
            query += " WHERE received_at BETWEEN ? AND ? ";
            params.push(start, end);
        } else if (start) {
            query += " WHERE received_at >= ? ";
            params.push(start);
        } else if (end) {
            query += " WHERE received_at <= ? ";
            params.push(end);
        }

        query += " GROUP BY survey_category";

        // Get total count separately
        let totalCountQuery = "SELECT COUNT(*) AS totalCount FROM feedback";
        let totalCountParams = [];

        if (start && end) {
            totalCountQuery += " WHERE received_at BETWEEN ? AND ? ";
            totalCountParams.push(start, end);
        } else if (start) {
            totalCountQuery += " WHERE received_at >= ? ";
            totalCountParams.push(start);
        } else if (end) {
            totalCountQuery += " WHERE received_at <= ? ";
            totalCountParams.push(end);
        }

        const [catRows] = await db.execute(query, params);
        const [countRows] = await db.execute(totalCountQuery, totalCountParams);

        const categories = catRows.map(row => ({
            categoryName: row.survey_category || "Uncategorized",
            count: row.count
        }));

        res.json({
            totalCount: countRows[0].totalCount,
            categories
        });
    } catch (error) {
        console.error("Metrics error:", error);
        res.status(500).json({ message: "Internal server error." });
    }
});

router.post("/posts", authenticateToken, async (req, res) => {
    const { db_id, post_title, post_body } = req.body;

    if (!db_id || !post_title || !post_body) {
        return res.status(400).json({ message: "DB ID, title, and body are required." });
    }

    try {
        const sql = "INSERT INTO posts (db_id, post_title, post_body) VALUES (?, ?, ?)";
        const [result] = await db.execute(sql, [db_id, post_title, post_body]);

        console.log('Insert result:', result);

        res.status(201).json({ message: "Post created successfully", postId: result.insertId });
    } catch (error) {
        console.error("Database error:", error);
        res.status(500).json({ message: `Internal server error: ${error.message}` }); 
    }
});


router.get("/posts", authenticateApiKey, authenticateToken, async (req, res) => {
    try {

        const [rows] = await db.execute("SELECT * FROM posts ORDER BY created_at DESC");
        res.json(rows);
    } catch (error) {
        console.error("Database error:", error);
        res.status(500).json({ message: "Internal server error." });
    }
});






module.exports = router;