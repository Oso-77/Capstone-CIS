//We may need to update this. I dont know if we should be requiring API key to see web pages. Also we need 

const express = require("express");
const { authenticateToken, authenticateApiKey } = require("../middlewares/auth-middleware");
const path = require('path');
const db = require("../utils/db");
const jwt = require('jsonwebtoken');
const bcryptjs = require('bcryptjs')
const { spawn } = require('child_process');
 


const router = express.Router();

router.use(express.static(path.join(__dirname, '../../../../Frontend')));

router.get('/form', (req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend', 'survey.html'));
});

router.get('/admin-home',(req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend', 'admin-home.html'));
});

router.get('/login', (req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend', 'login.html'));
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


router.get('/admin-post', authenticateApiKey, (req, res) => {
    res.sendFile(path.join(__dirname + '../../../../Frontend', 'admin-post.html'));

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



router.delete('/posts/:postId', authenticateApiKey, async (req, res) => {
    try {
      const { postId } = req.params;
  
      if (!postId) {
        return res.status(400).json({ message: 'Post ID is required' });
      }
  
      
      const query = 'DELETE FROM posts WHERE post_id = ?';
      const result = await db.query(query, [postId]);
  
      if (result.rowCount === 0) {
        return res.status(404).json({ message: 'Post not found' });
      }
  
      res.json({ message: 'Post deleted successfully' });
    } catch (error) {
      console.error('Error deleting post:', error);
      res.status(500).json({ message: 'Error deleting post' });
    }
  });
 // router.post("/process-feedback", authenticateToken, authenticateApiKey, (req, res) => {
router.post("/run-gpt", (req, res) => {
    // Spawn a new child process to call the Python script
    const pythonProcess = spawn("python", [
      "../gpt_integration/gpt_integration.py",  // Adjust path if necessary
      "process_feedback"
    ]);
    // Capture stdout
    pythonProcess.stdout.on("data", (data) => {
      console.log(`stdout: ${data}`);
    });
    // Capture stderr
    pythonProcess.stderr.on("data", (data) => {
      console.error(`stderr: ${data}`);
    });
    // When the process is done, respond to the client
    pythonProcess.on("close", (code) => {
      console.log(`Python script exited with code ${code}`);
      if (code === 0) {
        return res.status(200).send("Feedback processing completed successfully.");
      } else {
        return res.status(500).send("Feedback processing failed. Check server logs for details.");
      }
    });
  });

  

router.delete('/response', authenticateApiKey, async (req, res) => {
    try {
      const query = 'DELETE FROM responses';
      const [result] = await db.execute(query);
  
      if (result.affectedRows === 0) {
        return res.status(404).json({ message: 'No rows to delete' });
      }
  
      res.json({ message: 'All rows deleted successfully' });
  
    } catch (error) {
      console.error('Error deleting data:', error);
      res.status(500).json({ message: 'Error deleting data' });
    }
  });


  
  
  
  






module.exports = router;