const dotenv = require("dotenv");

dotenv.config();

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

module.exports = authenticateApiKey;
