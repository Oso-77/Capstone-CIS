const express = require("express");
const authenticateToken = require("../middlewares/auth-middleware");
const path = require('path');
const db = require("../utils/db");

const router = express.Router();

router.use(express.static(path.join(__dirname, '../../../../Frontend')));

router.get('/form', (req, res) =>{
    res.sendFile(path.join(__dirname + '../../../../Frontend', 'index.html'));
});

// POST
router.post("/feedback", authenticateToken, async (req, res) => {
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

// GET
router.get("/feedback", authenticateToken, async (req, res) => {
    try {
        const [rows] = await db.execute("SELECT * FROM feedback");
        res.json(rows);
    } catch (error) {
        console.error("Database error:", error);
        res.status(500).json({ message: "Internal server error." });
    }
});

module.exports = router;
