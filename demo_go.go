package main

import (
	"fmt"
	"time"
)

// UserService provides user management functionality
type UserService struct {
	users map[string]*User
}

// CreateUser creates a new user in the system
// Parameters:
//   - username: The unique username
//   - email: The user's email address
//   - name: The user's display name
//
// Returns the created User and any error
func (s *UserService) CreateUser(username, email, name string) (*User, error) {
	user := &User{
		ID:        generateUserID(),
		Name:      name,
		Email:     email,
		CreatedAt: time.Now(),
		IsActive:  true,
	}

	s.users[username] = user
	return user, nil
}

// GetUser retrieves a user by username
func (s *UserService) GetUser(username string) (*User, error) {
	user, exists := s.users[username]
	if !exists {
		return nil, fmt.Errorf("user not found: %s", username)
	}
	return user, nil
}

// ActivateUser activates a user account
func (s *UserService) ActivateUser(username string) error {
	user, err := s.GetUser(username)
	if err != nil {
		return err
	}
	user.IsActive = true
	return nil
}

// DeactivateUser deactivates a user account
func (s *UserService) DeactivateUser(username string) error {
	user, err := s.GetUser(username)
	if err != nil {
		return err
	}
	user.IsActive = false
	return nil
}

// GetDisplayName returns the user's formatted display name
func (u *User) GetDisplayName() string {
	return fmt.Sprintf("%s (%s)", u.Name, u.Email)
}

// generateUserID generates a unique user identifier
func generateUserID() string {
	return fmt.Sprintf("user_%d_%d", time.Now().Unix(), time.Now().UnixNano()%1000000)
}

// ProcessData processes user data and returns a summary
func ProcessData(users []*User) map[string]interface{} {
	activeCount := 0
	for _, user := range users {
		if user.IsActive {
			activeCount++
		}
	}

	return map[string]interface{}{
		"total":       len(users),
		"active":      activeCount,
		"inactive":    len(users) - activeCount,
		"processedAt": time.Now(),
	}
}

func main() {
	service := NewUserService()
	
	user, err := service.CreateUser("john_doe", "john@example.com", "John Doe")
	if err != nil {
		fmt.Printf("Error creating user: %v\n", err)
		return
	}
	
	fmt.Printf("Created user: %s\n", user.GetDisplayName())
}

