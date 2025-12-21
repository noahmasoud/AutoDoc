package main

import "fmt"

// TestFunction is a test function
func TestFunction(param1 string, param2 int) string {
	return fmt.Sprintf("%s: %d", param1, param2)
}

// TestType is a test type
type TestType struct {
	Name  string
	Value int
}

// TestInterface is a test interface
type TestInterface interface {
	DoSomething() error
}

// TestConst is a test constant
const TestConst = "test"

// TestVar is a test variable
var TestVar = 42

func main() {
	fmt.Println("Hello, World!")
}

