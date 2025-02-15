const dotenv = require("dotenv");
const jwt = require('jsonwebtoken')

dotenv.config();

const authenticateToken = (req, res, next) => {
    const token = req.header("Authorization") && req.header("Authorization").split(' ')[1];

    if (!token) {
        return res.status(403).json({ message: "Access denied, no token provided." });
    }

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        req.user = decoded;
        next();
    } catch (error) {
        res.status(400).json({ message: "Invalid token." });
    }
};

const authenticateApiKey = (req, res, next) => {
    const apiKey = process.env.API_KEY;

    if (!apiKey) {
        return res.status(401).json({ message: "Access denied. No API key provided." });
    }

    if (apiKey !== process.env.API_KEY) {
        return res.status(403).json({ message: "Invalid API key." });
    }

    next();
};

module.exports = { authenticateApiKey, authenticateToken };