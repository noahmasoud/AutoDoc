package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
)

// Symbol represents an extracted symbol from Go code
type Symbol struct {
	Name     string `json:"name"`
	Type     string `json:"type"`
	Line     int    `json:"line"`
	Doc      string `json:"doc,omitempty"`
	Exported bool   `json:"exported"`
}

// ASTResult represents the parsed AST result
type ASTResult struct {
	Success bool              `json:"success"`
	AST     *FileAST          `json:"ast,omitempty"`
	Error   *ErrorInfo        `json:"error,omitempty"`
	Symbols map[string][]Symbol `json:"symbols,omitempty"`
}

// FileAST represents the file-level AST structure
type FileAST struct {
	Package string   `json:"package"`
	Imports []string `json:"imports,omitempty"`
	Body    []Node   `json:"body,omitempty"`
}

// Node represents an AST node
type Node struct {
	Type string                 `json:"type"`
	Name string                 `json:"name,omitempty"`
	Line int                    `json:"line,omitempty"`
	Data map[string]interface{} `json:"data,omitempty"`
}

// ErrorInfo represents error information
type ErrorInfo struct {
	Message string `json:"message"`
	Line    int    `json:"line,omitempty"`
}

func main() {
	if len(os.Args) < 2 {
		// Read from stdin
		sourceCode, err := readStdin()
		if err != nil {
			outputError("Failed to read from stdin: " + err.Error())
			os.Exit(1)
		}
		parseAndOutput(sourceCode, "<stdin>")
	} else {
		// Read from file
		filePath := os.Args[1]
		sourceCode, err := os.ReadFile(filePath)
		if err != nil {
			outputError("Failed to read file: " + err.Error())
			os.Exit(1)
		}
		parseAndOutput(string(sourceCode), filePath)
	}
}

func readStdin() (string, error) {
	var sourceCode string
	buf := make([]byte, 4096)
	for {
		n, err := os.Stdin.Read(buf)
		if n > 0 {
			sourceCode += string(buf[:n])
		}
		if err != nil {
			if err.Error() == "EOF" {
				break
			}
			return "", err
		}
	}
	return sourceCode, nil
}

func parseAndOutput(sourceCode, filename string) {
	fset := token.NewFileSet()
	
	// Parse the file
	file, err := parser.ParseFile(fset, filename, sourceCode, parser.ParseComments)
	if err != nil {
		outputError("Parse error: " + err.Error())
		os.Exit(1)
	}

	// Build AST result
	result := ASTResult{
		Success: true,
		AST:     buildFileAST(file, fset),
		Symbols: extractSymbols(file, fset),
	}

	// Output JSON
	jsonData, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		outputError("Failed to marshal JSON: " + err.Error())
		os.Exit(1)
	}

	fmt.Println(string(jsonData))
}

func buildFileAST(file *ast.File, fset *token.FileSet) *FileAST {
	fileAST := &FileAST{
		Package: file.Name.Name,
		Body:    []Node{},
	}

	// Extract imports
	for _, imp := range file.Imports {
		importPath := ""
		if imp.Path != nil {
			importPath = imp.Path.Value
		}
		fileAST.Imports = append(fileAST.Imports, importPath)
	}

	// Extract declarations
	for _, decl := range file.Decls {
		node := buildNodeFromDecl(decl, fset)
		if node != nil {
			fileAST.Body = append(fileAST.Body, *node)
		}
	}

	return fileAST
}

func buildNodeFromDecl(decl ast.Decl, fset *token.FileSet) *Node {
	switch d := decl.(type) {
	case *ast.GenDecl:
		return buildNodeFromGenDecl(d, fset)
	case *ast.FuncDecl:
		return buildNodeFromFuncDecl(d, fset)
	}
	return nil
}

func buildNodeFromGenDecl(decl *ast.GenDecl, fset *token.FileSet) *Node {
	if len(decl.Specs) == 0 {
		return nil
	}

	spec := decl.Specs[0]
	pos := fset.Position(decl.Pos())

	switch s := spec.(type) {
	case *ast.TypeSpec:
		return &Node{
			Type: "TypeDeclaration",
			Name: s.Name.Name,
			Line: pos.Line,
			Data: map[string]interface{}{
				"exported": s.Name.IsExported(),
			},
		}
	case *ast.ValueSpec:
		if len(s.Names) > 0 {
			return &Node{
				Type: getValueSpecType(decl.Tok),
				Name: s.Names[0].Name,
				Line: pos.Line,
				Data: map[string]interface{}{
					"exported": s.Names[0].IsExported(),
				},
			}
		}
	}

	return nil
}

func buildNodeFromFuncDecl(decl *ast.FuncDecl, fset *token.FileSet) *Node {
	pos := fset.Position(decl.Pos())
	nodeType := "FunctionDeclaration"
	if decl.Recv != nil {
		nodeType = "MethodDeclaration"
	}

	name := ""
	if decl.Name != nil {
		name = decl.Name.Name
	}

	return &Node{
		Type: nodeType,
		Name: name,
		Line: pos.Line,
		Data: map[string]interface{}{
			"exported": decl.Name != nil && decl.Name.IsExported(),
		},
	}
}

func getValueSpecType(tok token.Token) string {
	switch tok {
	case token.CONST:
		return "ConstDeclaration"
	case token.VAR:
		return "VarDeclaration"
	default:
		return "ValueDeclaration"
	}
}

func extractSymbols(file *ast.File, fset *token.FileSet) map[string][]Symbol {
	symbols := map[string][]Symbol{
		"functions": []Symbol{},
		"types":     []Symbol{},
		"interfaces": []Symbol{},
		"structs":   []Symbol{},
		"consts":   []Symbol{},
		"vars":     []Symbol{},
	}

	// Extract package-level symbols
	for _, decl := range file.Decls {
		switch d := decl.(type) {
		case *ast.FuncDecl:
			if d.Name != nil {
				pos := fset.Position(d.Pos())
				symbolType := "function"
				if d.Recv != nil {
					symbolType = "method"
				}
				symbol := Symbol{
					Name:     d.Name.Name,
					Type:     symbolType,
					Line:     pos.Line,
					Doc:      extractDoc(d.Doc),
					Exported: d.Name.IsExported(),
				}
				if symbolType == "function" {
					symbols["functions"] = append(symbols["functions"], symbol)
				} else {
					symbols["functions"] = append(symbols["functions"], symbol)
				}
			}
		case *ast.GenDecl:
			for _, spec := range d.Specs {
				switch s := spec.(type) {
				case *ast.TypeSpec:
					pos := fset.Position(s.Pos())
					symbolType := "type"
					if _, isInterface := s.Type.(*ast.InterfaceType); isInterface {
						symbolType = "interface"
						symbols["interfaces"] = append(symbols["interfaces"], Symbol{
							Name:     s.Name.Name,
							Type:     "interface",
							Line:     pos.Line,
							Doc:      extractDoc(d.Doc),
							Exported: s.Name.IsExported(),
						})
					} else if _, isStruct := s.Type.(*ast.StructType); isStruct {
						symbolType = "struct"
						symbols["structs"] = append(symbols["structs"], Symbol{
							Name:     s.Name.Name,
							Type:     "struct",
							Line:     pos.Line,
							Doc:      extractDoc(d.Doc),
							Exported: s.Name.IsExported(),
						})
					} else {
						symbols["types"] = append(symbols["types"], Symbol{
							Name:     s.Name.Name,
							Type:     symbolType,
							Line:     pos.Line,
							Doc:      extractDoc(d.Doc),
							Exported: s.Name.IsExported(),
						})
					}
				case *ast.ValueSpec:
					pos := fset.Position(s.Pos())
					for _, name := range s.Names {
						if d.Tok == token.CONST {
							symbols["consts"] = append(symbols["consts"], Symbol{
								Name:     name.Name,
								Type:     "const",
								Line:     pos.Line,
								Doc:      extractDoc(d.Doc),
								Exported: name.IsExported(),
							})
						} else if d.Tok == token.VAR {
							symbols["vars"] = append(symbols["vars"], Symbol{
								Name:     name.Name,
								Type:     "var",
								Line:     pos.Line,
								Doc:      extractDoc(d.Doc),
								Exported: name.IsExported(),
							})
						}
					}
				}
			}
		}
	}

	return symbols
}

func extractDoc(commentGroup *ast.CommentGroup) string {
	if commentGroup == nil {
		return ""
	}
	doc := ""
	for _, comment := range commentGroup.List {
		doc += comment.Text + "\n"
	}
	return doc
}

func outputError(message string) {
	result := ASTResult{
		Success: false,
		Error: &ErrorInfo{
			Message: message,
		},
	}
	jsonData, _ := json.Marshal(result)
	fmt.Fprintln(os.Stderr, string(jsonData))
}

