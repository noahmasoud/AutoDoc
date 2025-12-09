# AutoDoc-1 Complete Class Diagram

```mermaid
classDiagram
    %% ============================================================================
    %% FRONTEND - Angular Components
    %% ============================================================================
    class AppComponent {
        +string title
        +boolean showNavbar
        +updateNavbarVisibility() void
    }
    
    class NavbarComponent {
        +boolean isAuthenticated
        +string currentRoute
        +boolean menuOpen
        +logout() void
        +isActive(route: string) boolean
        +toggleMenu() void
    }
    
    class DashboardComponent {
        +string connectionStatus
        +string connectionUrl
        +number rulesCount
        +number templatesCount
        +boolean isLoading
        +loadDashboardData() void
    }
    
    class ConnectionsComponent {
        +FormGroup connectionForm
        +boolean isTokenSaved
        +boolean isTesting
        +Connection existingConnection
        +StatusMessage statusMessage
        +loadConnection() void
        +saveConnection() void
        +testConnection() void
    }
    
    class RulesComponent {
        +Rule[] rules
        +TemplateSummary[] templates
        +FormGroup ruleForm
        +boolean isEditMode
        +boolean isCreating
        +number editingRuleId
        +boolean isLoading
        +boolean isSubmitting
        +loadRules() void
        +loadTemplates() void
        +createRule() void
        +updateRule() void
        +deleteRule() void
    }
    
    class TemplatesComponent {
        +TemplateSummary[] templates
        +loadTemplates() void
    }
    
    class LoginComponent {
        +FormGroup loginForm
        +boolean isLoading
        +string errorMessage
        +onSubmit() void
    }
    
    class RunDetailsComponent {
        +string runId
        +ChangeReport report
        +boolean isLoading
        +loadReport() void
    }
    
    %% ============================================================================
    %% FRONTEND - Services
    %% ============================================================================
    class AuthService {
        -string TOKEN_KEY
        -string API_URL
        -BehaviorSubject authStatusSubject
        +login(username: string, password: string) Observable~LoginResponse~
        +logout() void
        +isLoggedIn() boolean
        +getToken() string | null
        +getAuthStatus() Observable~boolean~
        -checkTokenValidity() void
    }
    
    class ConnectionsService {
        -string apiUrl
        +getConnection() Observable~Connection | null~
        +saveConnection(connection: ConnectionCreate) Observable~Connection~
        +testConnection(request: ConnectionTestRequest) Observable~ConnectionTestResponse~
    }
    
    class RulesService {
        -string apiUrl
        +listRules() Observable~Rule[]~
        +createRule(rule: RuleRequest) Observable~Rule~
        +updateRule(ruleId: number, payload: Partial~RuleRequest~) Observable~Rule~
        +deleteRule(ruleId: number) Observable~void~
    }
    
    class TemplatesService {
        -string apiUrl
        +listTemplates() Observable~TemplateSummary[]~
    }
    
    class ChangeReportService {
        -string apiUrl
        +getRunReport(runId: string) Observable~ChangeReport~
    }
    
    %% ============================================================================
    %% FRONTEND - Guards & Interceptors
    %% ============================================================================
    class AuthGuard {
        +canActivate(route, state) boolean
    }
    
    class AuthInterceptor {
        +intercept(req, next) Observable
    }
    
    %% ============================================================================
    %% BACKEND - API Routers
    %% ============================================================================
    class HealthRouter {
        +GET /api/v1/health() HealthResponse
    }
    
    class AuthRouter {
        +POST /api/login(request: LoginRequest) LoginResponse
        +GET /api/login/userinfo() UserInfo
        +GET /api/login() UserInfo
    }
    
    class ConnectionsRouter {
        +POST /api/connections(payload: ConnectionCreate) ConnectionOut
        +GET /api/connections() ConnectionOut | None
        +POST /api/connections/test(payload: ConnectionTestRequest) ConnectionTestResponse
        -_normalize_base_url(url: str) str
    }
    
    class RulesRouter {
        +GET /api/v1/rules() List~RuleOut~
        +POST /api/v1/rules(payload: RuleCreate) RuleOut
        +GET /api/v1/rules/{id}(rule_id: int) RuleOut
        +PUT /api/v1/rules/{id}(rule_id: int, payload: RuleUpdate) RuleOut
        +DELETE /api/v1/rules/{id}(rule_id: int) void
    }
    
    class TemplatesRouter {
        +GET /api/v1/templates() List~TemplateOut~
        +POST /api/v1/templates(payload: TemplateCreate) TemplateOut
        +GET /api/v1/templates/{id}(template_id: int) TemplateOut
        +PUT /api/v1/templates/{id}(template_id: int, payload: TemplateUpdate) TemplateOut
        +DELETE /api/v1/templates/{id}(template_id: int) void
    }
    
    class RunsRouter {
        +GET /api/v1/runs(page: int, page_size: int) RunsPage
        +POST /api/v1/runs(payload: RunCreate) RunOut
        +GET /api/v1/runs/{id}(run_id: int) RunOut
        +POST /api/v1/runs/{id}/report(run_id: int, request: ChangeReportRequest) ChangeReportResponse
    }
    
    class PatchesRouter {
        +GET /api/v1/patches() List~PatchOut~
        +PUT /api/v1/patches/{id}(patch_id: int, payload: PatchUpdate) PatchOut
    }
    
    class DiffParserRouter {
        +POST /api/diff/parse(request: DiffRequest) DiffResponse
    }
    
    %% ============================================================================
    %% BACKEND - Core Services
    %% ============================================================================
    class ChangeReportGenerator {
        +generate_change_report(run_id: int) ChangeReport
    }
    
    class PatchGenerator {
        +generate_patches_for_run(run_id: int) List~Patch~
    }
    
    class RulesEngine {
        +match_rule(selector: str, file_path: str) bool
        +validate_selector(selector: str) void
    }
    
    class TemplateEngine {
        +render_template(template: Template, variables: dict) str
    }
    
    class ConfluenceClient {
        +test_connection(base_url: str, space_key: str, token: str) bool
        +get_space(space_key: str) dict
        +publish_page(page_id: str, content: str) bool
    }
    
    %% ============================================================================
    %% BACKEND - Security Services
    %% ============================================================================
    class EncryptionService {
        +encrypt_token(token: str) str
        +decrypt_token(encrypted_token: str) str
        -_derive_key(secret_key: str, salt: bytes) bytes
    }
    
    class TokenMasking {
        +mask_token(token: str | None, visible_chars: int) str
        +mask_payload(payload: dict, keys: List~str~) dict
        +mask_dict_keys(data: dict, keys_to_mask: List~str~) dict
    }
    
    class SecurityMiddleware {
        +dispatch(request: Request, call_next) Response
        -_log_request_safely(request: Request) void
        -_log_response_safely(request: Request, response: Response) void
        -_log_error_safely(request: Request, error: Exception) void
        -_is_sensitive_endpoint(path: str) bool
        -_mask_headers(headers: dict) dict
        -_mask_string(text: str) str
    }
    
    class CorrelationIdMiddleware {
        +dispatch(request: Request, call_next) Response
    }
    
    class ErrorHandlers {
        +install_handlers(app: FastAPI) void
        +validation_handler(request, exc) JSONResponse
        +http_handler(request, exc) JSONResponse
        +integrity_handler(request, exc) JSONResponse
        +sa_handler(request, exc) JSONResponse
        +general_handler(request, exc) JSONResponse
    }
    
    %% ============================================================================
    %% DATABASE MODELS
    %% ============================================================================
    class Run {
        +int id
        +str repo
        +str branch
        +str commit_sha
        +datetime started_at
        +datetime completed_at
        +str status
        +str correlation_id
        +bool is_dry_run
        +str mode
        +List~Change~ changes
        +List~Patch~ patches
        +List~PythonSymbol~ python_symbols
    }
    
    class Change {
        +int id
        +int run_id
        +str file_path
        +str symbol
        +str change_type
        +dict signature_before
        +dict signature_after
        +Run run
    }
    
    class Patch {
        +int id
        +int run_id
        +str page_id
        +str diff_before
        +str diff_after
        +str diff_unified
        +dict diff_structured
        +str approved_by
        +datetime applied_at
        +str status
        +dict error_message
        +Run run
    }
    
    class Rule {
        +int id
        +str name
        +str selector
        +str space_key
        +str page_id
        +int template_id
        +bool auto_approve
        +int priority
        +Template template
    }
    
    class Template {
        +int id
        +str name
        +str format
        +str body
        +dict variables
        +List~Rule~ rules
    }
    
    class Connection {
        +int id
        +str confluence_base_url
        +str space_key
        +str encrypted_token
        +datetime last_used_at
        +datetime created_at
        +datetime updated_at
    }
    
    class PythonSymbol {
        +int id
        +int run_id
        +str file_path
        +str symbol_name
        +str qualified_name
        +str symbol_type
        +str docstring
        +int lineno
        +dict symbol_metadata
        +Run run
    }
    
    %% ============================================================================
    %% SCHEMAS (Pydantic Models)
    %% ============================================================================
    class ConnectionCreate {
        +AnyHttpUrl confluence_base_url
        +str space_key
        +str api_token
    }
    
    class ConnectionOut {
        +int id
        +str confluence_base_url
        +str space_key
        +datetime last_used_at
        +datetime created_at
        +datetime updated_at
    }
    
    class ConnectionTestRequest {
        +AnyHttpUrl confluence_base_url
        +str space_key
        +str api_token
    }
    
    class ConnectionTestResponse {
        +bool ok
        +str details
        +datetime timestamp
    }
    
    class RuleCreate {
        +str name
        +str selector
        +str space_key
        +str page_id
        +int template_id
        +bool auto_approve
    }
    
    class RuleOut {
        +int id
        +str name
        +str selector
        +str space_key
        +str page_id
        +int template_id
        +bool auto_approve
    }
    
    class TemplateCreate {
        +str name
        +str format
        +str body
        +dict variables
    }
    
    class TemplateOut {
        +int id
        +str name
        +str format
        +str body
        +dict variables
    }
    
    class RunCreate {
        +str repo
        +str branch
        +str commit_sha
        +str correlation_id
        +bool is_dry_run
        +str mode
    }
    
    class RunOut {
        +int id
        +str repo
        +str branch
        +str commit_sha
        +datetime started_at
        +datetime completed_at
        +str status
        +str correlation_id
    }
    
    %% ============================================================================
    %% FASTAPI APPLICATION
    %% ============================================================================
    class FastAPI {
        +title: str
        +version: str
        +include_router(router) void
        +add_middleware(middleware) void
    }
    
    %% ============================================================================
    %% RELATIONSHIPS - Frontend
    %% ============================================================================
    AppComponent --> NavbarComponent : contains
    AppComponent --> AuthService : uses
    NavbarComponent --> AuthService : uses
    
    DashboardComponent --> ConnectionsService : uses
    DashboardComponent --> RulesService : uses
    DashboardComponent --> TemplatesService : uses
    
    ConnectionsComponent --> ConnectionsService : uses
    RulesComponent --> RulesService : uses
    RulesComponent --> TemplatesService : uses
    TemplatesComponent --> TemplatesService : uses
    LoginComponent --> AuthService : uses
    RunDetailsComponent --> ChangeReportService : uses
    
    ConnectionsService --> AuthInterceptor : uses
    RulesService --> AuthInterceptor : uses
    TemplatesService --> AuthInterceptor : uses
    ChangeReportService --> AuthInterceptor : uses
    AuthService --> AuthInterceptor : uses
    
    AuthGuard --> AuthService : checks
    
    %% ============================================================================
    %% RELATIONSHIPS - Backend
    %% ============================================================================
    FastAPI --> HealthRouter : includes
    FastAPI --> AuthRouter : includes
    FastAPI --> ConnectionsRouter : includes
    FastAPI --> RulesRouter : includes
    FastAPI --> TemplatesRouter : includes
    FastAPI --> RunsRouter : includes
    FastAPI --> PatchesRouter : includes
    FastAPI --> DiffParserRouter : includes
    
    FastAPI --> CorrelationIdMiddleware : uses
    FastAPI --> SecurityMiddleware : uses
    FastAPI --> ErrorHandlers : uses
    
    ConnectionsRouter --> Connection : manages
    ConnectionsRouter --> EncryptionService : uses
    ConnectionsRouter --> TokenMasking : uses
    ConnectionsRouter --> ConfluenceClient : uses
    
    RulesRouter --> Rule : manages
    RulesRouter --> RulesEngine : uses
    
    TemplatesRouter --> Template : manages
    TemplatesRouter --> TemplateEngine : uses
    
    RunsRouter --> Run : manages
    RunsRouter --> Change : manages
    RunsRouter --> Patch : manages
    RunsRouter --> ChangeReportGenerator : uses
    RunsRouter --> PatchGenerator : uses
    
    PatchGenerator --> Rule : uses
    PatchGenerator --> Template : uses
    PatchGenerator --> TemplateEngine : uses
    
    ChangeReportGenerator --> Run : processes
    ChangeReportGenerator --> Change : analyzes
    
    SecurityMiddleware --> TokenMasking : uses
    ErrorHandlers --> TokenMasking : uses
    
    %% ============================================================================
    %% RELATIONSHIPS - Database
    %% ============================================================================
    Run "1" *-- "0..*" Change : has
    Run "1" *-- "0..*" Patch : generates
    Run "1" *-- "0..*" PythonSymbol : contains
    Rule "0..*" --> "0..1" Template : uses
    
    %% ============================================================================
    %% RELATIONSHIPS - Schemas
    %% ============================================================================
    ConnectionsRouter ..> ConnectionCreate : accepts
    ConnectionsRouter ..> ConnectionOut : returns
    ConnectionsRouter ..> ConnectionTestRequest : accepts
    ConnectionsRouter ..> ConnectionTestResponse : returns
    
    RulesRouter ..> RuleCreate : accepts
    RulesRouter ..> RuleOut : returns
    
    TemplatesRouter ..> TemplateCreate : accepts
    TemplatesRouter ..> TemplateOut : returns
    
    RunsRouter ..> RunCreate : accepts
    RunsRouter ..> RunOut : returns
    
    %% ============================================================================
    %% RELATIONSHIPS - Frontend to Backend
    %% ============================================================================
    ConnectionsService ..> ConnectionsRouter : HTTP calls
    RulesService ..> RulesRouter : HTTP calls
    TemplatesService ..> TemplatesRouter : HTTP calls
    AuthService ..> AuthRouter : HTTP calls
    ChangeReportService ..> RunsRouter : HTTP calls
    
    %% ============================================================================
    %% STYLING
    %% ============================================================================
    classDef frontend fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px
    classDef backend fill:#E1F5FE,stroke:#2196F3,stroke-width:2px
    classDef database fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px
    classDef security fill:#FFF3E0,stroke:#FF9800,stroke-width:2px
    classDef schema fill:#FCE4EC,stroke:#E91E63,stroke-width:2px
    
    class AppComponent,NavbarComponent,DashboardComponent,ConnectionsComponent,RulesComponent,TemplatesComponent,LoginComponent,RunDetailsComponent frontend
    class AuthService,ConnectionsService,RulesService,TemplatesService,ChangeReportService,AuthGuard,AuthInterceptor frontend
    
    class FastAPI,HealthRouter,AuthRouter,ConnectionsRouter,RulesRouter,TemplatesRouter,RunsRouter,PatchesRouter,DiffParserRouter backend
    class ChangeReportGenerator,PatchGenerator,RulesEngine,TemplateEngine,ConfluenceClient backend
    
    class Run,Change,Patch,Rule,Template,Connection,PythonSymbol database
    
    class EncryptionService,TokenMasking,SecurityMiddleware,CorrelationIdMiddleware,ErrorHandlers security
    
    class ConnectionCreate,ConnectionOut,ConnectionTestRequest,ConnectionTestResponse,RuleCreate,RuleOut,TemplateCreate,TemplateOut,RunCreate,RunOut schema
```

