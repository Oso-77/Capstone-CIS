const { createFeedback, getAllFeedback, addLeaderResponse } = require('../controllers/feedback-controller');

// Handle POST
const create = async (req, res) => {
    try {
        const { feedback, comment1, comment2, comment3 } = req.body;
        const userId = req.user.userId;  // From decoded JWT
        await createFeedback(feedback, comment1, comment2, comment3);
        res.status(201).json({ message: 'Feedback submitted successfully' });
    } catch (err) {
        res.status(500).json({ error: 'Failed to submit feedback' });
    }
};

// Handle GET
const getAll = async (req, res) => {
    try {
        const feedback = await getAllFeedback();
        res.json(feedback);
    } catch (err) {
        res.status(500).json({ error: 'Failed to retrieve feedback' });
    }
};

// Handle POST for Leader's response
const respondToFeedback = async (req, res) => {
    const { responseId, leaderResponse } = req.body;
    try {
        await addLeaderResponse(responseId, leaderResponse);
        res.status(200).json({ message: 'Leader response added successfully' });
    } catch (err) {
        res.status(500).json({ error: 'Failed to add leader response' });
    }
};

module.exports = { create, getAll, respondToFeedback };


