const db = require('../utils/db');

// Function to create feedback in the database
const createFeedback = (feedback, comment1, comment2, comment3) => {
    return new Promise((resolve, reject) => {
        const query = 'INSERT INTO feedback (feedback, comment1, comment2, comment3) VALUES (?, ?, ?, ?)';
        db.query(query, [feedback, comment1, comment2, comment3], (err, results) => {
            if (err) return reject(err);
            resolve(results);
        });
    });
};

// Function to get all feedback from the database
const getAllFeedback = () => {
    return new Promise((resolve, reject) => {
        const query = 'SELECT * FROM feedback';
        db.query(query, (err, results) => {
            if (err) return reject(err);
            resolve(results);
        });
    });
};

module.exports = { createFeedback, getAllFeedback };
