const bcrypt = require('bcryptjs');

// Function to hash a password
async function hashPassword() {
    const plainTextPassword = 'regPassword';  

    const saltRounds = 10; 

    try {
        const hashedPassword = await bcrypt.hash(plainTextPassword, saltRounds);
        console.log("Hashed Password: ", hashedPassword);
    } catch (error) {
        console.error("Error hashing password:", error);
    }
}

hashPassword();
