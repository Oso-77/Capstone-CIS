const express = require('express');
const bodyParser = require('body-parser');
const feedbackRoutes = require('./routes/feedback-routes');
const cors = require('cors');

require('dotenv').config();

const app = express();

app.use(cors());
app.use(bodyParser.json());  // Parse JSON

// Feedback routes
app.use('/api', feedbackRoutes);

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
