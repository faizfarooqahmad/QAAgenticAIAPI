---
name: QA API Testing Agent
version: 1.0.0
description: An agentic AI assistant for QA engineers to test REST APIs through natural language chat.
author: QA Team
tags: [api-testing, qa, rest, crud, automation]
---

# Skills

## Skill: JSONPlaceholder API

- **Base URL:** https://jsonplaceholder.typicode.com
- **Auth Required:** No
- **Description:** A free fake REST API for testing and prototyping CRUD operations. No authentication required. Returns simulated data for users, posts, comments, and todos.

### Tool: list_users

- **Method:** GET
- **Endpoint:** /users
- **Description:** Fetch all users (10 total)

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| — | — | — | — | No parameters required |

#### Examples

```prompt
List all users from JSONPlaceholder
```

```prompt
Show me all the users available in the system
```

---

### Tool: get_user

- **Method:** GET
- **Endpoint:** /users/{user_id}
- **Description:** Fetch a single user by ID

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| user_id | int | Yes | — | User ID (1-10) |

#### Examples

```prompt
Get user with ID 3
```

```prompt
Fetch details of user number 5 from JSONPlaceholder
```

---

### Tool: list_posts

- **Method:** GET
- **Endpoint:** /posts
- **Description:** Fetch all posts, optionally filtered by user

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| user_id | int | No | — | Filter posts by user ID |

#### Examples

```prompt
List all posts from JSONPlaceholder
```

```prompt
Show me all posts written by user 2
```

---

### Tool: get_post

- **Method:** GET
- **Endpoint:** /posts/{post_id}
- **Description:** Fetch a single post by ID

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| post_id | int | Yes | — | Post ID |

#### Examples

```prompt
Get post number 7
```

```prompt
Fetch the post with ID 15 from JSONPlaceholder
```

---

### Tool: create_post

- **Method:** POST
- **Endpoint:** /posts
- **Description:** Create a new post (simulated — returns the created object)

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| title | str | Yes | — | Title of the post |
| body | str | Yes | — | Body content of the post |
| user_id | int | No | 1 | Author user ID |

#### Examples

```prompt
Create a new post with title "Login Bug" and body "Login page returns 500 error on submit"
```

```prompt
Create a post titled "Test Results" with body "All regression tests passed" for user 3
```

---

### Tool: update_post

- **Method:** PUT
- **Endpoint:** /posts/{post_id}
- **Description:** Update an existing post by ID (simulated)

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| post_id | int | Yes | — | ID of the post to update |
| title | str | Yes | — | New title |
| body | str | Yes | — | New body content |

#### Examples

```prompt
Update post 1 with new title "Updated Title" and body "This is the corrected content"
```

```prompt
Change post 5 title to "Fixed Issue" and body to "The bug has been resolved"
```

---

### Tool: delete_post

- **Method:** DELETE
- **Endpoint:** /posts/{post_id}
- **Description:** Delete a post by ID (simulated)

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| post_id | int | Yes | — | ID of the post to delete |

#### Examples

```prompt
Delete post number 10
```

```prompt
Remove post with ID 3 from JSONPlaceholder
```

---

### Tool: get_comments

- **Method:** GET
- **Endpoint:** /posts/{post_id}/comments
- **Description:** Fetch all comments for a post

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| post_id | int | Yes | — | Post ID to get comments for |

#### Examples

```prompt
Get all comments on post 1
```

```prompt
Show me the comments for post number 12
```

---

### Tool: list_todos

- **Method:** GET
- **Endpoint:** /todos
- **Description:** Fetch all todos, optionally filtered by user

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| user_id | int | No | — | Filter todos by user ID |

#### Examples

```prompt
List all todos from JSONPlaceholder
```

```prompt
Show me todos for user 5
```

---

## Skill: Generic REST API Caller

- **Base URL:** Any
- **Auth Required:** Optional
- **Description:** Call any REST API endpoint with full control over HTTP method, headers, query parameters, request body, and authentication.

### Tool: call_rest_api

- **Method:** ANY (GET, POST, PUT, PATCH, DELETE)
- **Endpoint:** User-specified URL
- **Description:** Call any REST API endpoint with custom configuration

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| method | str | Yes | — | HTTP method: GET, POST, PUT, PATCH, DELETE |
| url | str | Yes | — | Full URL of the API endpoint |
| headers_json | str | No | {} | JSON string of extra headers |
| query_params_json | str | No | {} | JSON string of query parameters |
| body_json | str | No | {} | JSON string of request body (POST/PUT/PATCH) |
| auth_type | str | No | none | Authentication type: none, api_key, bearer, basic |
| auth_value | str | No | — | The key/token/base64 value for auth |

#### Authentication Types

| Type | Description | How It Works |
|------|-------------|--------------|
| none | No authentication | Default — no auth headers added |
| api_key | API Key authentication | Adds `?api_key=<value>` as query parameter |
| bearer | Bearer / OAuth Token | Adds `Authorization: Bearer <value>` header |
| basic | Basic Authentication | Adds `Authorization: Basic <value>` header (Base64 user:pass) |

#### Examples

```prompt
Call GET on https://httpbin.org/get
```

```prompt
Make a GET request to https://jsonplaceholder.typicode.com/albums
```

```prompt
Call GET on https://httpbin.org/get with query params {"page": "1", "limit": "10"}
```

```prompt
Call POST on https://httpbin.org/post with body {"username": "testuser", "email": "test@example.com"}
```

```prompt
Make a POST request to https://reqres.in/api/users with body {"name": "John", "job": "QA Engineer"}
```

```prompt
Call PUT on https://reqres.in/api/users/2 with body {"name": "Jane", "job": "Senior QA"}
```

```prompt
Call PATCH on https://reqres.in/api/users/2 with body {"job": "Lead QA"}
```

```prompt
Call DELETE on https://reqres.in/api/users/2
```

```prompt
Call GET on https://api.example.com/users with bearer token "eyJhbGciOiJIUzI1NiIsInR5..."
```

```prompt
Make a POST to https://api.example.com/orders with bearer auth token "my-oauth-token" and body {"item": "widget", "qty": 5}
```

```prompt
Call GET on https://api.example.com/data with API key "abc123xyz"
```

```prompt
Call GET on https://httpbin.org/basic-auth/user/pass with basic auth "dXNlcjpwYXNz"
```

```prompt
Call GET on https://httpbin.org/headers with headers {"X-Custom-Header": "QA-Test", "Accept": "application/json"}
```

---

## Skill: Response Analysis

- **Base URL:** N/A
- **Auth Required:** No
- **Description:** Analyse, compare, and validate API responses for QA purposes. Can check schemas, find missing fields, compare multiple responses, and provide PASS/FAIL summaries.

### Capabilities

- Validate response schema and field types
- Detect missing or null fields
- Compare two or more API responses
- Summarise findings with PASS/FAIL indicators
- Suggest follow-up test cases

### Examples

```prompt
Analyse the last response — are there any missing fields?
```

```prompt
Compare the response of get user 1 and get user 2 — what are the differences?
```

```prompt
Validate the response schema — does every user have an email and phone field?
```

```prompt
Is the status code correct for a delete operation?
```

```prompt
Check if all posts have a non-empty title and body
```
