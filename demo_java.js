/**
 * Demo JavaScript File
 * 
 * This file demonstrates JavaScript code analysis capabilities
 * for the AutoDoc system.
 */

/**
 * User Service Module
 * Provides user management functionality
 */

/**
 * Creates a new user in the system
 * @param {string} username - The unique username
 * @param {string} email - The user's email address
 * @param {Object} options - Additional user options
 * @returns {Promise<User>} The created user object
 */
async function createUser(username, email, options = {}) {
    const user = {
        id: generateUserId(),
        username,
        email,
        createdAt: new Date(),
        ...options
    };
    
    // Save to database
    await saveUserToDatabase(user);
    
    return user;
}

/**
 * User class for managing user data and operations
 */
class User {
    /**
     * Creates a new User instance
     * @param {string} id - User ID
     * @param {string} name - User's display name
     * @param {string} email - User's email
     */
    constructor(id, name, email) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.isActive = true;
    }
    
    /**
     * Gets the user's full display name
     * @returns {string} The formatted display name
     */
    getDisplayName() {
        return `${this.name} (${this.email})`;
    }
    
    /**
     * Activates the user account
     */
    activate() {
        this.isActive = true;
    }
    
    /**
     * Deactivates the user account
     */
    deactivate() {
        this.isActive = false;
    }
}

/**
 * Utility function to generate a unique user ID
 * @returns {string} A unique user identifier
 */
function generateUserId() {
    return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Saves a user to the database
 * @param {User} user - The user object to save
 * @returns {Promise<void>}
 */

// Export functions and classes
export { createUser, User, generateUserId };

