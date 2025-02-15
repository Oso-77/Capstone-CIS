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


router.get('/dashboard', authenticateApiKey, (req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend', 'dashboard.html'));

});

router.get('/main', authenticateApiKey, (req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend/response_board', 'main.html'));

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

const { addLeaderResponse } = require('../controllers/feedback-controller');

router.post("/response", authenticateToken, async (req, res) => {
    const { responseId, leaderResponse } = req.body;
    if (!responseId || !leaderResponse) {
        return res.status(400).json({ message: "Response ID and leader response are required." });
    }
    try {
        await addLeaderResponse(responseId, leaderResponse);
        res.status(200).json({ message: 'Leader response added successfully' });
    } catch (error) {
        console.error("Database error:", error);
        res.status(500).json({ message: "Internal server error." });
    }
});


// GET - Fetch feedback (Protected)
// Do we need to auth the token here? Commented it out for now
router.get("/feedback", authenticateApiKey,
    // authenticateToken, 
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
    // authenticateToken, 
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

module.exports = router;